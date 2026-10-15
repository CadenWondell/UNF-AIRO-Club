"""``load_kit`` and ``Kit``: the student-facing entry point (plan § 4).

``Kit.load()`` runs cohort → labels → index times → features → leakage checks →
``min_features_present`` → patient-level split. The test partition stays hidden.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from clinical_ml_kits.cohort.labels import build_cohort
from clinical_ml_kits.core.errors import KitValidationError
from clinical_ml_kits.core.kit_schema import (
    LoadedKit,
    ValidationContext,
    ValidationReport,
    load_kit_definition,
    rule_concepts,
    validate_kit,
)
from clinical_ml_kits.core.logging import get_logger, log_environment_selected
from clinical_ml_kits.core.paths import project_root
from clinical_ml_kits.core.run_manifest import RunManifest, framework_git_commit
from clinical_ml_kits.core.values import PROVISIONAL_BANNER, Provisional
from clinical_ml_kits.data.policy import policy_for
from clinical_ml_kits.data.registry import get_adapter
from clinical_ml_kits.features.matrix import FeatureMatrixBuilder, FeatureRequest, Kind
from clinical_ml_kits.leakage import checks
from clinical_ml_kits.splitting.cv import PatientGroupedKFold, make_cv_splitter
from clinical_ml_kits.splitting.datasets import KitData, make_kit_data
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

_log = get_logger("kit")
DATA_SOURCES = {"synthetic": "synthetic", "all_of_us": "all_of_us_workbench"}


@dataclass(frozen=True)
class FeatureSpec:
    numeric: tuple[str, ...]
    categorical: tuple[str, ...]

    @property
    def columns(self) -> tuple[str, ...]:
        return self.numeric + self.categorical


def _find_root(start: Path) -> Path:
    for d in [start, *start.parents]:
        if (d / "definitions").is_dir() and (d / "synthetic").is_dir():
            return d
    return project_root()


def _locate(kit: str | Path, root: Path | None) -> tuple[Path, Path]:
    p = Path(kit)
    if p.exists():
        f = p / "kit.yaml" if p.is_dir() else p
        return f, Path(root) if root else _find_root(f.resolve().parent)
    kit_id = str(kit)
    here = Path(os.getcwd()) / "kit.yaml"
    if here.is_file() and load_kit_definition(here).kit_id == kit_id:
        return here, Path(root) if root else _find_root(here.resolve().parent)
    base = Path(root) if root else project_root()
    for f in sorted((base / "kits").rglob("kit.yaml")):
        if load_kit_definition(f).kit_id == kit_id:
            return f, base
    raise KeyError(f"no kit with id {kit_id!r} under {base / 'kits'}")


def load_kit(
    kit: str | Path, data_source: str = "synthetic", *, root: str | Path | None = None
) -> Kit:
    """Load and validate a kit for a data source (``synthetic`` or ``all_of_us``).

    ``all_of_us`` is refused outside the All of Us Researcher Workbench before any data access,
    and requires the ``workbench`` validation level (no provisional values).
    """
    if data_source not in DATA_SOURCES:
        raise ValueError(f"data_source must be one of {sorted(DATA_SOURCES)}")
    environment = DATA_SOURCES[data_source]
    path, base = _locate(kit, Path(root) if root else None)
    ctx = ValidationContext.from_root(base)
    loaded = load_kit_definition(path)
    adapter = get_adapter("all_of_us", root=base) if data_source == "all_of_us" else None
    report = validate_kit(loaded, policy_for(environment).required_validation_level, ctx)
    log_environment_selected(kit_id=loaded.kit_id, environment=environment)
    return Kit(loaded, ctx, data_source, report, adapter)


class Kit:
    def __init__(
        self,
        loaded: LoadedKit,
        ctx: ValidationContext,
        data_source: str,
        report: ValidationReport,
        adapter: Any = None,
    ) -> None:
        self._loaded = loaded
        self.ctx = ctx
        self.data_source = data_source
        self.environment = DATA_SOURCES[data_source]
        self.validation = report
        self._adapter = adapter
        self._data: KitData | None = None

    # ------------------------------------------------------------------ identity
    @property
    def kit_id(self) -> str:
        return self._loaded.kit_id

    @property
    def definition(self) -> Any:
        return self._loaded.definition

    @property
    def phenotype(self) -> Any:
        return self._loaded.phenotype

    @property
    def adapter(self) -> Any:
        if self._adapter is None:
            params = self.ctx.root / str(self.definition.synthetic_population)
            self._adapter = get_adapter(
                "synthetic_clinical", backend="population", params=params, root=self.ctx.root
            )
        return self._adapter

    @property
    def temporal_policy(self) -> ResolvedTemporalPolicy:
        return ResolvedTemporalPolicy.from_schema(self.definition.temporal_policy)

    # ------------------------------------------------------------------ features
    def feature_requests(self) -> list[FeatureRequest]:
        reg = self.ctx.registry
        out = []
        for f in self.definition.features:
            e = reg.get(f.feature)
            kind: Kind
            if e.domain == "person":
                kind = "person_categorical" if e.value_type == "categorical" else "person"
            elif e.value_type == "event":
                kind = "event"
            else:
                kind = "numeric"
            out.append(FeatureRequest(f.feature, e.concept.id, kind, list(f.derivations), f.window))
        return out

    @property
    def feature_spec(self) -> FeatureSpec:
        num: list[str] = []
        cat: list[str] = []
        for r in self.feature_requests():
            cols = [f"{r.name}__{d}" for d in r.derivations]
            (cat if r.kind == "person_categorical" else num).extend(cols)
        return FeatureSpec(tuple(num), tuple(cat))

    def _excluded_concepts(self) -> set[str]:
        d = self.definition
        return set(self.phenotype.label_defining_concepts) | {
            p.concept for p in d.prohibited if p.concept
        }

    def _label_source_concepts(self) -> set[str]:
        ph = self.phenotype
        out = rule_concepts(ph.case_rule) | rule_concepts(ph.control_rule)
        if ph.repeat_evidence is not None:
            out |= rule_concepts(ph.repeat_evidence)
        return out

    def _leakage_checks(self, lineage: pd.DataFrame, cohort: pd.DataFrame) -> None:
        d = self.definition
        justified = {j.item for j in d.justified_inclusions}
        reqs = self.feature_requests()
        fc = {r.name: r.concept for r in reqs}
        checks.check_target_overlap(fc, self.phenotype.label_defining_concepts, justified)
        checks.check_label_sources(fc, self._label_source_concepts(), justified)
        reg = self.ctx.registry
        checks.check_prohibited(
            {r.name: (r.concept, reg.get(r.name).domain) for r in reqs},
            [p.model_dump(exclude_none=True) for p in d.prohibited],
            justified,
        )
        checks.check_lineage(lineage, cohort, self.temporal_policy)

    # ------------------------------------------------------------------ load
    def load(self) -> KitData:
        d, ph = self.definition, self.phenotype
        cohort = build_cohort(ph, d.cohort, self.adapter)
        table = cohort.table
        if not table.person_id.is_unique:
            raise KitValidationError(
                "phenotype",
                "binary_tabular current_state kits require one row per person; "
                f"{int(table.person_id.duplicated().sum())} duplicate person rows found",
            )
        index = table[["person_id", "index_time", "index_visit_id"]]
        builder = FeatureMatrixBuilder(
            self.adapter,
            self.feature_requests(),
            self.temporal_policy,
            excluded_concepts=frozenset(self._excluded_concepts()),
        )
        X, lineage = builder.build(index)
        self._leakage_checks(lineage, index)
        keep = self._min_features_present(X)
        table = table[table.person_id.isin(keep)].reset_index(drop=True)
        sp = d.split
        data = make_kit_data(
            table,
            X,
            salt=sp.salt,
            fractions=tuple(sp.fractions),
            environment=self.environment,
            kit_id=self.kit_id,
            salt_version=sp.salt_version,
            kit_version=d.kit_version,
            min_positives=sp.min_positives_per_partition,
            tolerance=sp.prevalence_tolerance,
        )
        data.feature_spec = self.feature_spec
        data.run_manifest = self._run_manifest(data, cohort.counts)
        self._data = data
        return data

    def _min_features_present(self, X: pd.DataFrame) -> list[str]:
        k = self.definition.missingness.min_features_present or 0
        present = pd.DataFrame(index=X.index)
        for r in self.feature_requests():
            cols = [f"{r.name}__{d}" for d in r.derivations]
            sub = X[cols]
            counts = [c for c in cols if c.endswith("__count")]
            informative = sub.notna() & ~((sub == 0) & sub.columns.isin(counts))
            present[r.name] = informative.any(axis=1)
        n_present = present.sum(axis=1)
        keep = list(n_present[n_present >= k].index)
        _log.info(
            "min_features_present=%d: excluded %d of %d rows before splitting",
            k,
            len(X) - len(keep),
            len(X),
        )
        return keep

    def _run_manifest(self, data: KitData, counts: dict[str, int]) -> RunManifest:
        d = self.definition
        concepts = sorted({r.concept for r in self.feature_requests()} | self.phenotype.concepts())
        versions = {}
        for c in concepts:
            try:
                versions[c] = self.adapter.resolve(c).version
            except Exception:
                versions[c] = "unresolved"
        pop = None
        if self.data_source == "synthetic":
            from clinical_ml_kits.data.registry import validate_population_params

            params = validate_population_params(self.ctx.root / str(d.synthetic_population))
            pop = {
                "path": str(d.synthetic_population),
                "seed": params.seed,
                "n_persons": params.n_persons,
            }
        md = self.adapter.metadata()
        return RunManifest(
            git_commit=framework_git_commit(),
            kit_id=self.kit_id,
            kit_definition_hash=self._loaded.content_hash(),
            kit_version=d.kit_version,
            phenotype_version=self.phenotype.version,
            concept_set_versions=versions,
            feature_registry_version=self.ctx.registry.registry_version,
            dataset_id=md.id,
            dataset_version=md.version,
            adapter=md.id,
            environment=self.environment,
            seed=d.seed,
            split_salt=d.split.salt,
            split_salt_version=d.split.salt_version,
            split_manifest_digest=data.split_manifest.digest,
            control_sampling_seed=self.phenotype.control_sampling.seed,
            synthetic_population=pop,
        )

    # ------------------------------------------------------------------ helpers
    def describe(self) -> str:
        d = self.definition
        lines = [
            f"Kit: {d.name} ({self.kit_id} v{d.kit_version}, status {d.status})",
            f"Question: {d.clinical_question.strip()}",
            f"Target: {d.target.label} ({d.target.code}) · prediction type: {d.prediction_type}"
            " (horizon: none)",
            f"Data source: {self.data_source} ({self.environment})",
            "Excluded from model input (label-defining / prohibited):",
        ]
        for c in sorted(self.phenotype.label_defining_concepts):
            lines.append(f"  - {c} (label-defining concept)")
        for p in d.prohibited:
            what = p.feature or p.concept or p.domain
            lines.append(f"  - {what}: {p.reason}")
        if self.validation.provisional:
            lines.append(f"{PROVISIONAL_BANNER}:")
            from clinical_ml_kits.core.kit_schema import _states

            for path, v in _states(self._loaded):
                if isinstance(v, Provisional):
                    lines.append(f"  - {path} = {v.provisional} (pending {v.pending})")
        lines.append(
            "Educational/research use only: not a clinically validated risk score, "
            "diagnosis, or treatment recommendation."
        )
        return "\n".join(lines)

    def patient(self, person_id: str) -> Any:
        from clinical_ml_kits.features.timeline import PatientTimeline

        return PatientTimeline.from_adapter(self.adapter, person_id)

    def cv_splitter(self, n_splits: int = 5) -> PatientGroupedKFold:
        """Patient-grouped folds within the training partition; pass ``groups=``."""
        return make_cv_splitter(n_splits=n_splits, seed=self.definition.seed)

    def calibrate_grouped(self, model: Any, method: str = "sigmoid") -> Any:
        """Grouped out-of-fold calibration on the training partition (V-14 pattern)."""
        from clinical_ml_kits.evaluation.grouped_calibration import calibrate_grouped

        data = self._require_data()
        return calibrate_grouped(
            model,
            data.train.X,
            data.train.y,
            data.train.groups,
            cv=self.cv_splitter(),
            method=method,
        )

    def _require_data(self) -> KitData:
        if self._data is None:
            raise RuntimeError("call kit.load() first")
        return self._data

    def __repr__(self) -> str:
        return f"Kit({self.kit_id!r}, data_source={self.data_source!r})"
