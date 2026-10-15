"""T084: case/control/index construction, control sampling, one row per person."""

from __future__ import annotations

import inspect
from pathlib import Path

import pandas as pd
import pytest

from clinical_ml_kits.cohort.labels import build_cohort
from clinical_ml_kits.core.kit_schema import ControlSampling, load_kit_definition
from clinical_ml_kits.data.registry import get_adapter
from clinical_ml_kits.features.matrix import FeatureMatrixBuilder, FeatureRequest
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

FIX = Path(__file__).resolve().parents[2] / "fixtures"
KIT = load_kit_definition(FIX / "kits" / "valid" / "provisional_kit.yaml")
PH, COH = KIT.phenotype, KIT.definition.cohort
GOLD = get_adapter(
    "synthetic_clinical", backend="golden", golden=[FIX / "golden" / "cohort_rules.yaml"], root=FIX
)
POP = get_adapter(
    "synthetic_clinical",
    backend="population",
    params=FIX / "synthetic" / "generator_params" / "fixture_kit.yaml",
    root=FIX,
)
NOTE = "Test value for synthetic execution and tests only; not an approved clinical rule."
EXP = {"cases": {"SYN-C-CASE": "2024-06-01", "SYN-C-LATECASE": "2024-04-01"}}


def sampling(
    strategy: str, ratio: float | None = None, seed: int = 11, match_on: list[str] | None = None
) -> object:
    return ControlSampling.model_validate(
        {
            "strategy": strategy,
            "controls_per_case": None
            if ratio is None
            else {"provisional": ratio, "note": NOTE, "pending": "V-20"},
            "match_on": match_on or [],
            "seed": seed,
            "rationale": "test",
            "provenance": [
                {
                    "source_id": "fixture_methods",
                    "locator": "x",
                    "application": "x",
                    "verification_status": "requires_verification",
                }
            ],
        }
    )


def phen(cs: object) -> object:
    return PH.model_copy(update={"control_sampling": cs})


def test_golden_cases_controls_and_neither() -> None:
    r = build_cohort(phen(sampling("all_eligible")), COH, GOLD)
    t = r.table.set_index("person_id")
    cases = t[t.label == 1]
    assert {k: str(v.date()) for k, v in cases.index_time.items()} == EXP["cases"]
    assert t.loc["SYN-C-CASE", "index_visit_id"] == "SYN-V-CASE-2"
    assert t.loc["SYN-C-LATECASE", "index_visit_id"] == "SYN-V-LC-4"
    assert list(t[t.label == 0].index) == ["SYN-C-CONTROL"]
    assert t.loc["SYN-C-CONTROL", "index_visit_id"] in {"SYN-V-CT-2", "SYN-V-CT-3"}
    for pid in ("SYN-C-NEARMISS", "SYN-C-NOEVIDENCE", "SYN-C-SHORTHIST", "SYN-C-MINOR"):
        assert pid not in t.index
    assert r.counts["eligible_controls"] == 1


def test_min_history_enforced() -> None:
    r = build_cohort(phen(sampling("all_eligible")), COH, GOLD)
    assert "SYN-C-SHORTHIST" not in set(r.table.person_id)
    assert r.counts["excluded_min_history"] >= 1


@pytest.mark.parametrize(
    "strategy,ratio,match_on",
    [
        ("all_eligible", None, None),
        ("random_ratio", 2.0, None),
        ("matched", 1.0, ["visit_type", "calendar_year", "sex_at_birth"]),
    ],
)
def test_one_row_per_person_and_reproducible(
    strategy: str, ratio: float | None, match_on: list[str] | None
) -> None:
    ph = phen(sampling(strategy, ratio, match_on=match_on))
    a, b = build_cohort(ph, COH, POP), build_cohort(ph, COH, POP)
    assert a.table.person_id.is_unique
    pd.testing.assert_frame_equal(a.table, b.table)
    n_case = int((a.table.label == 1).sum())
    n_ctrl = int((a.table.label == 0).sum())
    assert n_case > 20 and n_ctrl > 20
    assert a.sampled_prevalence == pytest.approx(n_case / (n_case + n_ctrl))
    if strategy == "random_ratio":
        assert n_ctrl == min(round(2.0 * n_case), a.counts["eligible_controls"])
    if strategy == "all_eligible":
        assert n_ctrl == a.counts["eligible_controls"]


def test_seed_changes_sample() -> None:
    a = build_cohort(phen(sampling("random_ratio", 1.0, seed=1)), COH, POP)
    b = build_cohort(phen(sampling("random_ratio", 1.0, seed=2)), COH, POP)
    assert set(a.table[a.table.label == 0].person_id) != set(b.table[b.table.label == 0].person_id)


def test_matched_controls_match_their_case() -> None:
    attrs = ["visit_type", "calendar_year", "sex_at_birth"]
    r = build_cohort(phen(sampling("matched", 1.0, match_on=attrs)), COH, POP)
    t = r.table.set_index("person_id")
    ctrl = t[t.label == 0]
    assert ctrl.matched_case.notna().all()
    for pid, row in ctrl.iterrows():
        case = t.loc[row.matched_case]
        for a in attrs:
            assert row[a] == case[a], (pid, a)


def test_labels_do_not_change_features() -> None:
    assert "label" not in inspect.signature(FeatureMatrixBuilder.build).parameters
    r = build_cohort(phen(sampling("random_ratio", 1.0)), COH, POP)
    pol = ResolvedTemporalPolicy.from_values(
        same_day="exclude_index_day", washout="P0D", lookback="P1095D", exclude_index_encounter=True
    )
    feats = [FeatureRequest("fx_bmi", "fx_bmi", "numeric", ["latest", "mean"])]
    cohort = r.table[["person_id", "index_time", "index_visit_id"]]
    X1, _ = FeatureMatrixBuilder(POP, feats, pol).build(cohort)
    flipped = r.table.assign(label=1 - r.table.label)
    X2, _ = FeatureMatrixBuilder(POP, feats, pol).build(
        flipped[["person_id", "index_time", "index_visit_id"]]
    )
    pd.testing.assert_frame_equal(X1, X2)
