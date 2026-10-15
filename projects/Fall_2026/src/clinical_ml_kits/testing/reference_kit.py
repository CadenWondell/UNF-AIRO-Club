"""Generic checks shared by every binary_tabular current_state kit test suite.

Kit test files supply only kit-specific expectations (in their golden fixtures); the checking
logic lives here once, so adding a kit adds data and tests, not new infrastructure.
"""

from __future__ import annotations

import copy
import shutil
from functools import cached_property
from pathlib import Path
from typing import Any
from unittest import mock

import pandas as pd
import yaml

from clinical_ml_kits import load_kit
from clinical_ml_kits.cohort.labels import build_cohort
from clinical_ml_kits.core.errors import KitValidationError, TargetLeakageError
from clinical_ml_kits.core.kit_schema import (
    ControlSampling,
    ValidationContext,
    load_kit_definition,
    validate_kit,
)
from clinical_ml_kits.data.registry import get_adapter
from clinical_ml_kits.features.matrix import FeatureMatrixBuilder
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy


class ReferenceKitChecks:
    def __init__(self, kit_dir: Path, golden_dir: Path, root: Path) -> None:
        self.kit_dir = Path(kit_dir)
        self.golden_dir = Path(golden_dir)
        self.root = Path(root)

    # ------------------------------------------------------------------ fixtures
    @cached_property
    def kit(self) -> Any:
        return load_kit(self.kit_dir, data_source="synthetic", root=self.root)

    @cached_property
    def data(self) -> Any:
        return self.kit.load()

    def golden(self, name: str) -> dict[str, Any]:
        out: dict[str, Any] = yaml.safe_load((self.golden_dir / f"{name}.yaml").read_text())
        return out

    def golden_adapter(self, name: str) -> Any:
        return get_adapter(
            "synthetic_clinical",
            backend="golden",
            golden=[self.golden_dir / f"{name}.yaml"],
            root=self.root,
        )

    # ------------------------------------------------------------------ labels
    def cohort_from_golden(self, name: str) -> Any:
        ph = self.kit.phenotype
        all_eligible = ControlSampling(
            strategy="all_eligible",
            controls_per_case=None,
            match_on=[],
            seed=ph.control_sampling.seed,
            rationale="golden test: keep every eligible control",
            provenance=ph.control_sampling.provenance,
        )
        return build_cohort(
            ph.model_copy(update={"control_sampling": all_eligible}),
            self.kit.definition.cohort,
            self.golden_adapter(name),
        )

    def check_cohort(self, name: str) -> None:
        exp = self.golden(name)["expected"]
        t = self.cohort_from_golden(name).table.set_index("person_id")
        cases = {p: str(r.index_time.date()) for p, r in t[t.label == 1].iterrows()}
        assert cases == {k: str(v) for k, v in exp["cases"].items()}, cases
        controls = t[t.label == 0]
        assert set(controls.index) == set(exp["controls"]), sorted(controls.index)
        for pid, visits in exp["controls"].items():
            assert controls.loc[pid, "index_visit_id"] in visits, pid
        assert not set(exp["neither"]) & set(t.index)

    def check_case_index_visits(self, name: str) -> None:
        exp = self.golden(name)["expected"].get("case_index_visits", {})
        t = self.cohort_from_golden(name).table.set_index("person_id")
        for pid, visit in exp.items():
            assert t.loc[pid, "index_visit_id"] == visit, pid

    # ------------------------------------------------------------------ features
    def features_from_golden(self, name: str, same_day: str | None = None) -> pd.Series:
        g = self.golden(name)
        adapter = self.golden_adapter(name)
        pol = self.kit.temporal_policy
        if same_day:  # counterfactual policy: index day and index encounter both allowed
            pol = ResolvedTemporalPolicy(
                same_day,
                pol.washout,
                pol.lookback,
                same_day == "exclude_index_day",
                pol.windowed_exclusions,
            )
        idx = pd.DataFrame(g["index"])
        idx["index_time"] = pd.to_datetime(idx.index_time.astype(str))
        X, lineage = FeatureMatrixBuilder(
            adapter,
            self.kit.feature_requests(),
            pol,
            excluded_concepts=frozenset(self.kit._excluded_concepts()),
        ).build(idx)
        from clinical_ml_kits.leakage.checks import check_lineage

        check_lineage(lineage, idx, pol)
        return X.loc[g["expected"]["person"]]

    def check_features(self, name: str) -> None:
        exp = self.golden(name)["expected"]
        row = self.features_from_golden(name)
        for col, v in exp.get("values", {}).items():
            assert row[col] == v, (col, row[col])
        for col, bad in exp.get("never_values", {}).items():
            assert row[col] not in bad, (col, row[col])
        for prefix in exp.get("absent_column_prefixes", []):
            assert not any(c.startswith(prefix + "__") for c in row.index), prefix

    def check_same_day_rule(self, name: str, column: str, include_value: float) -> None:
        """Under ``include`` the index-day workup value would be visible; the kit excludes it."""
        assert self.features_from_golden(name, same_day="include")[column] == include_value
        assert self.features_from_golden(name)[column] != include_value

    def check_label_overlap_rejected(self) -> None:
        fc = {r.name: r.concept for r in self.kit.feature_requests()}
        label = sorted(self.kit.phenotype.label_defining_concepts)[0]
        fc["planted_label_feature"] = label
        from clinical_ml_kits.leakage.checks import check_target_overlap

        try:
            check_target_overlap(fc, self.kit.phenotype.label_defining_concepts, set())
        except TargetLeakageError:
            return
        raise AssertionError("label-defining concept overlap was not rejected")

    def check_target_features_excluded(self) -> None:
        cols = list(self.data.train.X.columns)
        for c in self.kit.phenotype.label_defining_concepts:
            assert not any(col.split("__")[0] == c for col in cols), c

    def check_two_row_rejected(self) -> None:
        import clinical_ml_kits.core.kit as kitmod

        real = vars(kitmod)["build_cohort"]

        def doubled(*a: Any, **k: Any) -> Any:
            r = real(*a, **k)
            r.table = pd.concat([r.table, r.table.iloc[[0]]], ignore_index=True)
            return r

        with mock.patch.object(kitmod, "build_cohort", doubled):
            try:
                self.kit.load()
            except KitValidationError as e:
                assert "one row per person" in str(e)
                return
        raise AssertionError("a two-row person was not rejected")

    # ------------------------------------------------------------------ synthetic population
    def check_partitions(self) -> None:
        d = self.data
        mp = self.kit.definition.split.min_positives_per_partition
        for p in ("train", "validation", "test"):
            s = d.split_manifest.partitions[p]
            assert s.n_pos >= mp and s.n - s.n_pos > 0, (p, s)
        ids = pd.concat([d.train.person_ids, d.validation.person_ids])
        assert ids.is_unique
        assert "golden" not in self.kit.adapter.source_label

    def check_groups_cv(self) -> None:
        import numpy as np

        d = self.data
        g = np.asarray(d.train.groups)
        assert len(g) == len(d.train.X) and not any("group" in c for c in d.train.X.columns)
        for tr, va in self.kit.cv_splitter().split(d.train.X, d.train.y, groups=d.train.groups):
            assert not set(g[tr]) & set(g[va])

    def check_sampling_reproducible(self) -> None:
        a = build_cohort(self.kit.phenotype, self.kit.definition.cohort, self.kit.adapter)
        b = build_cohort(self.kit.phenotype, self.kit.definition.cohort, self.kit.adapter)
        pd.testing.assert_frame_equal(a.table, b.table)
        m = self.data.split_manifest
        assert 0 < m.sampled_development_prevalence < 1

    def check_envelopes(self) -> None:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline

        from clinical_ml_kits.preprocessing import make_preprocessor

        d = self.data
        m = Pipeline(
            [
                ("preprocess", make_preprocessor(self.kit.feature_spec)),
                ("model", LogisticRegression(max_iter=1000)),
            ]
        ).fit(d.train.X, d.train.y)
        for e in self.kit.to_envelopes(m, d.validation.X.head(3)):
            assert e.prediction_type == "current_state" and e.horizon is None
            assert e.payload.probability_basis == "development_sample"

    # ------------------------------------------------------------------ provenance and status
    def check_provenance_report(self) -> None:
        from clinical_ml_kits.provenance.checks import check_kit, errors

        ctx = ValidationContext.from_root(self.root)
        assert errors(check_kit(self.kit_dir, ctx)) == []
        report = validate_kit(load_kit_definition(self.kit_dir), "synthetic", ctx)
        assert report.provisional, "reference kits currently carry provisional values"

    def check_levels(self) -> None:
        ctx = ValidationContext.from_root(self.root)
        kit = load_kit_definition(self.kit_dir)
        validate_kit(kit, "synthetic", ctx)
        try:
            validate_kit(kit, "workbench", ctx)
        except KitValidationError as e:
            assert "provisional" in str(e)
            return
        raise AssertionError("workbench level passed while values are provisional")

    def check_approved_rejected(self, tmp: Path) -> None:
        dst = tmp / "kit"
        shutil.copytree(self.kit_dir, dst)
        k = dst / "kit.yaml"
        k.write_text(k.read_text().replace("status: requires_verification", "status: approved", 1))
        try:
            validate_kit(load_kit_definition(dst), "schema", ValidationContext.from_root(self.root))
        except KitValidationError as e:
            assert "P-4" in str(e)
            return
        raise AssertionError("status approved accepted with provisional values")

    def check_notebook_executes(self) -> None:
        import nbformat
        from nbclient import NotebookClient

        nb = nbformat.read(self.kit_dir / "kit.ipynb", as_version=4)  # type: ignore[no-untyped-call]
        original = copy.deepcopy(nb)
        NotebookClient(
            nb,
            timeout=600,
            kernel_name="python3",
            resources={"metadata": {"path": str(self.kit_dir)}},
        ).execute()
        after = nbformat.read(self.kit_dir / "kit.ipynb", as_version=4)  # type: ignore[no-untyped-call]
        assert after == original, "executing the notebook must not modify the committed file"
