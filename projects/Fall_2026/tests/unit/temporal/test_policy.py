"""T070: effective-cutoff rules 1-4 (data-model § 2) on the same-day golden matrix."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from clinical_ml_kits.adapters.synthetic_clinical.golden import load_golden
from clinical_ml_kits.core.kit_schema import TemporalPolicy
from clinical_ml_kits.data.registry import get_adapter
from clinical_ml_kits.temporal.cutoff import effective_upper_bound, permitted_mask
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

GOLDEN = Path(__file__).resolve().parents[3] / "synthetic" / "golden" / "same_day_cases.yaml"
FX = load_golden(GOLDEN)
ADAPTER = get_adapter("synthetic_clinical", backend="golden", golden=[GOLDEN])
OBS = ADAPTER.observations(domain="measurement")
NOTE = "Test value for synthetic execution and tests only; not an approved clinical rule."


def _policy(spec: dict) -> ResolvedTemporalPolicy:
    return ResolvedTemporalPolicy.from_values(
        same_day=spec["same_day"],
        washout=spec["washout"],
        lookback=spec["lookback"],
        exclude_index_encounter=spec["exclude_index_encounter"],
        windowed_exclusions=spec.get("windowed_exclusions", []),
    )


@pytest.mark.parametrize("case", sorted(FX.expected))
def test_matrix(case: str) -> None:
    exp = FX.expected[case]
    pol = _policy(exp["policy"])
    mask = permitted_mask(OBS, FX.index, pol)
    assert sorted(OBS[mask].label) == sorted(exp["permitted"])
    assert "f_post_index" not in set(OBS[mask].label)


def test_upper_bound_for_adapter_pushdown() -> None:
    idx = pd.Timestamp("2026-01-01")
    inc = _policy(
        {
            "same_day": "include",
            "washout": "P0D",
            "lookback": "P365D",
            "exclude_index_encounter": False,
        }
    )
    exc = _policy(
        {
            "same_day": "exclude_index_day",
            "washout": "P1D",
            "lookback": "P365D",
            "exclude_index_encounter": False,
        }
    )
    assert effective_upper_bound(idx, inc) == pd.Timestamp("2026-01-02")
    assert effective_upper_bound(idx, exc) == pd.Timestamp("2025-12-31")


def test_date_only_rows_count_as_same_day() -> None:
    pol = _policy(
        {
            "same_day": "exclude_index_day",
            "washout": "P0D",
            "lookback": "P3650D",
            "exclude_index_encounter": False,
        }
    )
    mask = permitted_mask(OBS, FX.index, pol)
    assert "b_index_day_date_only" not in set(OBS[mask].label)


def test_same_day_required() -> None:
    with pytest.raises(ValidationError, match="same_day"):
        TemporalPolicy.model_validate(
            {
                "exclude_index_encounter": {"provisional": True, "note": NOTE, "pending": "V-20"},
                "washout": {"provisional": "P0D", "note": NOTE, "pending": "V-20"},
                "lookback": {"provisional": "P365D", "note": NOTE, "pending": "V-20"},
            }
        )


def test_from_schema_resolves_value_states_and_rejects_unverified() -> None:
    tp = TemporalPolicy.model_validate(
        {
            "same_day": {"provisional": "exclude_index_day", "note": NOTE, "pending": "V-20"},
            "exclude_index_encounter": {"provisional": True, "note": NOTE, "pending": "V-20"},
            "washout": {"provisional": "P0D", "note": NOTE, "pending": "V-20"},
            "lookback": "UNVERIFIED",
        }
    )
    with pytest.raises(ValueError, match="UNVERIFIED"):
        ResolvedTemporalPolicy.from_schema(tp)


def test_persons_without_index_get_nothing() -> None:
    pol = _policy(
        {
            "same_day": "include",
            "washout": "P0D",
            "lookback": "P3650D",
            "exclude_index_encounter": False,
        }
    )
    mask = permitted_mask(OBS, FX.index.iloc[0:0], pol)
    assert not mask.any()
