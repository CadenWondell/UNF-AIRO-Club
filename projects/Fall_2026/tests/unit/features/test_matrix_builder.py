"""T076: FeatureMatrixBuilder equals the patient view on every golden patient and derivation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from clinical_ml_kits.data.registry import get_adapter
from clinical_ml_kits.features.matrix import FeatureMatrixBuilder, FeatureRequest
from clinical_ml_kits.features.timeline import Missing, PatientTimeline
from clinical_ml_kits.temporal.cutoff import effective_upper_bound
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

GOLDEN = Path(__file__).resolve().parents[3] / "synthetic" / "golden"
A = get_adapter("synthetic_clinical", backend="golden", golden=sorted(GOLDEN.glob("*.yaml")))
DERIVS = [
    "latest",
    "previous",
    "delta",
    "pct_change",
    "mean",
    "rolling_mean(P365D)",
    "min",
    "max",
    "std",
    "slope",
    "count",
    "time_since_last",
]
FEATURES = [
    FeatureRequest("creatinine", "creatinine", "numeric", DERIVS),
    FeatureRequest("bmi", "bmi", "numeric", DERIVS),
    FeatureRequest("sodium", "sodium", "numeric", DERIVS),
    FeatureRequest("outpatient_visits", "visit_outpatient", "event", ["count", "time_since_last"]),
    FeatureRequest("age", "age", "person", ["latest"]),
    FeatureRequest("sex_at_birth", "sex_at_birth", "person_categorical", ["latest"]),
]
COHORT = pd.DataFrame(
    {
        "person_id": ["SYN-G-CREAT-001", "SYN-G-SD-001", "SYN-G-SPARSE-001", "SYN-G-MV-001"],
        "index_time": pd.to_datetime(["2026-01-01"] * 4),
        "index_visit_id": [None, "SYN-V-SD-IDX", "SYN-V-SP-2", None],
    }
)


@pytest.mark.parametrize("same_day", ["include", "exclude_index_day"])
def test_builder_equals_patient_view(same_day: str) -> None:
    pol = ResolvedTemporalPolicy.from_values(
        same_day=same_day, washout="P0D", lookback="P1095D", exclude_index_encounter=True
    )
    X, lineage = FeatureMatrixBuilder(A, FEATURES, pol).build(COHORT)
    for row in COHORT.itertuples():
        view = PatientTimeline.from_adapter(A, row.person_id).as_of(
            row.index_time, pol, index_visit_id=row.index_visit_id
        )
        for f in FEATURES:
            for d in f.derivations:
                col = f"{f.name}__{d}"
                got = X.loc[row.person_id, col]
                exp = view.derive(f.concept, d)
                if isinstance(exp, Missing):
                    assert pd.isna(got), (row.person_id, col, got)
                elif isinstance(exp, str):
                    assert got == exp, (row.person_id, col)
                else:
                    assert got == pytest.approx(exp), (row.person_id, col)
    # lineage: each used source time is before the row's effective (exclusive) upper bound
    for pid, rows in lineage.groupby("person_id"):
        bound = effective_upper_bound(pd.Timestamp("2026-01-01"), pol)
        assert (rows.max_source_time < bound).all(), pid


def test_creatinine_golden_values_in_matrix() -> None:
    inc = ResolvedTemporalPolicy.from_values(
        same_day="include", washout="P0D", lookback="P3650D", exclude_index_encounter=False
    )
    X, lineage = FeatureMatrixBuilder(A, FEATURES, inc).build(COHORT.iloc[[0]])
    r = X.loc["SYN-G-CREAT-001"]
    assert r["creatinine__latest"] == 1.2 and r["creatinine__previous"] == 1.0
    assert r["creatinine__delta"] == pytest.approx(0.2) and r["creatinine__count"] == 3
    assert (lineage.max_source_time < pd.Timestamp("2026-03-01")).all()


def test_columns_names_and_nan() -> None:
    pol = ResolvedTemporalPolicy.from_values(
        same_day="include", washout="P0D", lookback="P1095D", exclude_index_encounter=False
    )
    X, _ = FeatureMatrixBuilder(A, FEATURES, pol).build(COHORT)
    assert list(X.columns) == [f"{f.name}__{d}" for f in FEATURES for d in f.derivations]
    assert np.isnan(X.loc["SYN-G-SPARSE-001", "creatinine__latest"])
    assert X.loc["SYN-G-SPARSE-001", "creatinine__count"] == 0
    assert list(X.index) == list(COHORT.person_id)
