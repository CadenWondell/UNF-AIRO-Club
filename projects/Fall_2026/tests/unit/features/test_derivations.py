"""T074: derivations (present and missing cases) on the multi-visit golden patient."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from clinical_ml_kits.adapters.synthetic_clinical.golden import load_golden
from clinical_ml_kits.data.registry import get_adapter
from clinical_ml_kits.features.timeline import Missing, PatientTimeline
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

GOLDEN = Path(__file__).resolve().parents[3] / "synthetic" / "golden"
MV = load_golden(GOLDEN / "multi_visit_patient.yaml")
A = get_adapter("synthetic_clinical", backend="golden", golden=sorted(GOLDEN.glob("*.yaml")))
P = ResolvedTemporalPolicy.from_values(
    same_day="include", washout="P0D", lookback="P3650D", exclude_index_encounter=False
)
VIEW = PatientTimeline.from_adapter(A, "SYN-G-MV-001").as_of(pd.Timestamp("2026-01-01"), P)
SPARSE = PatientTimeline.from_adapter(A, "SYN-G-SPARSE-001").as_of(pd.Timestamp("2026-01-01"), P)
EXP = MV.expected["bmi"]


@pytest.mark.parametrize(
    "derivation,key",
    [
        ("latest", "latest"),
        ("previous", "previous"),
        ("delta", "delta"),
        ("pct_change", "pct_change"),
        ("mean", "mean"),
        ("min", "min"),
        ("max", "max"),
        ("count", "count"),
        ("std", "std"),
        ("time_since_last", "time_since_last"),
        ("rolling_mean(P365D)", "rolling_mean_P365D"),
    ],
)
def test_present(derivation: str, key: str) -> None:
    assert VIEW.derive("bmi", derivation) == pytest.approx(EXP[key])


def test_slope() -> None:
    days = np.array(
        [
            (pd.Timestamp(d) - pd.Timestamp("2026-01-01")).days
            for d in ("2024-01-01", "2024-07-01", "2025-07-01", "2025-12-01")
        ],
        dtype=float,
    )
    vals = np.array([30.0, 31.0, 33.0, 34.0])
    expected = np.polyfit(days, vals, 1)[0]
    assert VIEW.derive("bmi", "slope") == pytest.approx(expected)


@pytest.mark.parametrize("derivation", ["previous", "delta", "pct_change", "std", "slope"])
def test_missing_with_one_point(derivation: str) -> None:
    out = SPARSE.derive("bmi", derivation)
    assert isinstance(out, Missing)


@pytest.mark.parametrize(
    "derivation", ["latest", "mean", "min", "max", "time_since_last", "rolling_mean(P30D)"]
)
def test_missing_with_no_points(derivation: str) -> None:
    out = SPARSE.derive("creatinine", derivation)
    assert isinstance(out, Missing) and out.reason == "no_observation"


def test_count_zero_not_missing() -> None:
    assert SPARSE.derive("creatinine", "count") == 0


def test_rolling_window_empty_is_missing() -> None:
    out = VIEW.derive("bmi", "rolling_mean(P7D)")
    assert isinstance(out, Missing)


def test_values_are_never_nan_filled() -> None:
    out = SPARSE.derive("creatinine", "mean")
    assert not (isinstance(out, float) and math.isnan(out))
