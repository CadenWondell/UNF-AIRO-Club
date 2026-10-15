"""Synthetic clinical adapter (namespace ``synthetic``).

Backends:
- ``population`` (default for ``data_source="synthetic"``): the seeded generator driven by a kit's
  ``synthetic_population`` params; used for end-to-end model and notebook execution.
- ``golden``: hand-authored fixtures; used only by unit and edge-case tests.

All data here is artificial, not clinically realistic, and never derived from participant data.
Filters are applied in pandas with the same semantics the All of Us adapter pushes into SQL.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from clinical_ml_kits.core.errors import PendingVerification
from clinical_ml_kits.core.logging import get_logger
from clinical_ml_kits.core.paths import project_root
from clinical_ml_kits.data.adapter import DatasetMetadata
from clinical_ml_kits.data.policy import DataEnvironmentPolicy, policy_for
from clinical_ml_kits.data.schemas import OBSERVATION_COLUMNS, PERSON_COLUMNS, VISIT_COLUMNS
from clinical_ml_kits.features.concept_sets import ConceptRepository, ConceptSetRealization

ADAPTER_VERSION = "0.1.0"
_log = get_logger("adapters.synthetic")


class SyntheticClinicalAdapter:
    namespace = "synthetic"

    def __init__(
        self,
        persons: pd.DataFrame,
        raw_observations: pd.DataFrame,
        *,
        definitions_dir: Path,
        source_label: str,
        version: str = ADAPTER_VERSION,
    ) -> None:
        self._repo = ConceptRepository(definitions_dir)
        self._version = version
        self.source_label = source_label
        self.unit_rejections: dict[str, int] = {}
        self._persons = persons[PERSON_COLUMNS].copy()
        self._obs = self._normalize(raw_observations)

    # ------------------------------------------------------------------ construction
    @classmethod
    def create(
        cls,
        backend: str = "population",
        *,
        golden: Sequence[Path] | None = None,
        params: Path | None = None,
        root: Path | None = None,
    ) -> SyntheticClinicalAdapter:
        root = Path(root) if root else project_root()
        defs = root / "definitions"
        if backend == "golden":
            from clinical_ml_kits.adapters.synthetic_clinical.golden import load_golden

            fixtures = [load_golden(Path(p)) for p in (golden or [])]
            if not fixtures:
                raise ValueError("golden backend needs at least one fixture")
            persons = pd.concat([f.persons for f in fixtures], ignore_index=True)
            obs = pd.concat([f.observations for f in fixtures], ignore_index=True)
            return cls(persons, obs, definitions_dir=defs, source_label="golden")
        if backend == "population":
            from clinical_ml_kits.adapters.synthetic_clinical.generator import generate
            from clinical_ml_kits.adapters.synthetic_clinical.params import load_params

            if params is None:
                raise ValueError("population backend needs a params file")
            pop = generate(load_params(Path(params)))
            repo = ConceptRepository(defs)
            concepts = sorted(set(pop.observations.logical_concept))
            codes = {c: repo.realization("synthetic", c).codes[0] for c in concepts}
            obs = pop.observations.assign(concept_id=pop.observations.logical_concept.map(codes))
            return cls(
                pop.persons,
                obs.drop(columns="logical_concept"),
                definitions_dir=defs,
                source_label=f"population:{Path(params).name}",
                version=f"{ADAPTER_VERSION}+seed{pop.seed}",
            )
        raise ValueError(f"unknown synthetic backend {backend!r}")

    # ------------------------------------------------------------------ protocol
    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            id="synthetic_clinical",
            version=self._version,
            environment="synthetic",
            namespace=self.namespace,
            supports=frozenset({"measurement", "condition", "drug", "procedure", "visit"}),
        )

    def policy(self) -> DataEnvironmentPolicy:
        return policy_for("synthetic")

    def resolve(self, logical_concept: str) -> ConceptSetRealization:
        try:
            return self._repo.realization(self.namespace, logical_concept)
        except KeyError as e:
            raise PendingVerification("realization", str(e)) from None

    def resolve_in_namespace(self, namespace: str, logical_concept: str) -> ConceptSetRealization:
        if namespace != self.namespace:
            raise PendingVerification(
                "namespace", f"the synthetic adapter never resolves {namespace!r} realizations"
            )
        return self.resolve(logical_concept)

    def persons(self, person_ids: Sequence[str] | None = None) -> pd.DataFrame:
        p = self._persons
        if person_ids is not None:
            p = p[p.person_id.isin(list(person_ids))]
        return p.reset_index(drop=True)

    def observations(
        self,
        domain: str | None = None,
        concepts: Sequence[str] | None = None,
        person_ids: Sequence[str] | None = None,
        before: pd.Timestamp | None = None,
        after: pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        o = self._obs
        mask = pd.Series(True, index=o.index)
        if concepts is not None:
            for c in concepts:
                self.resolve(c)  # raises for concepts without a synthetic realization
            mask &= o.logical_concept.isin(list(concepts))
        if domain is not None:
            mask &= o.domain == domain
        if person_ids is not None:
            mask &= o.person_id.isin(list(person_ids))
        if before is not None:
            mask &= o.start_time < pd.Timestamp(before)
        if after is not None:
            mask &= o.start_time >= pd.Timestamp(after)
        return o[mask].reset_index(drop=True)

    def visits(
        self, person_ids: Sequence[str] | None = None, before: pd.Timestamp | None = None
    ) -> pd.DataFrame:
        v = self.observations(domain="visit", person_ids=person_ids, before=before)
        v = v.rename(columns={"logical_concept": "visit_type"})
        return v[VISIT_COLUMNS].reset_index(drop=True)

    def index_candidates(self, visit_concepts: Sequence[str] | None = None) -> pd.DataFrame:
        v = self.visits()
        if visit_concepts:
            v = v[v.visit_type.isin(list(visit_concepts))]
        out = pd.DataFrame(
            {
                "person_id": v.person_id,
                "index_time": v.start_time.dt.normalize(),
                "index_visit_id": v.visit_id,
                "visit_type": v.visit_type,
            }
        )
        return out.sort_values(["person_id", "index_time", "index_visit_id"]).reset_index(drop=True)

    # ------------------------------------------------------------------ internals
    def _code_map(self) -> dict[str, ConceptSetRealization]:
        out: dict[str, ConceptSetRealization] = {}
        for (ns, logical_id), _versions in sorted(self._repo.realizations.items()):
            if ns != self.namespace:
                continue
            real = self._repo.realization(ns, logical_id)
            for code in real.codes:
                out[code] = real
        return out

    def _normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        codes = self._code_map()
        df = raw.copy()
        for c in OBSERVATION_COLUMNS:
            if c not in df.columns:
                df[c] = None
        df["logical_concept"] = df.concept_id.map({c: r.logical_id for c, r in codes.items()})
        df["mapping_version"] = df.concept_id.map({c: r.version for c, r in codes.items()})
        unmapped = int(df.logical_concept.isna().sum())
        if unmapped:
            _log.info("synthetic adapter: %d rows with codes outside any realization", unmapped)
        df = df[df.logical_concept.notna()].copy()
        real = df.concept_id.map(codes)
        factor = [
            r.unit_factor(u) if d == "measurement" else 1.0
            for r, u, d in zip(real, df.unit_raw, df.domain, strict=True)
        ]
        df["_factor"] = factor
        rejected = df[df._factor.isna()]
        for concept, n in rejected.groupby("logical_concept").size().items():
            self.unit_rejections[str(concept)] = int(n)
            _log.info("unit rejected for %s: %d rows (unaccepted unit)", concept, n)
        df = df[df._factor.notna()].copy()
        df["value_num"] = pd.to_numeric(df.value_num, errors="coerce") * df._factor.astype(float)
        canonical = df.concept_id.map(lambda c: codes[c].canonical_unit)
        df["unit"] = canonical.where(df.domain == "measurement", None)
        df["start_time"] = pd.to_datetime(df.start_time)
        df["end_time"] = pd.to_datetime(df.end_time)
        df["source_table"] = df.source_table.fillna("synthetic_observations")
        cols = OBSERVATION_COLUMNS + (["label"] if "label" in df.columns else [])
        out = df[cols].sort_values(["person_id", "start_time", "concept_id"], kind="stable")
        return out.reset_index(drop=True)

    def __repr__(self) -> str:
        return f"SyntheticClinicalAdapter({self.source_label}, artificial data)"
