"""T150: kit-specific tests for aou_ckd_current (golden patients + synthetic population)."""

from __future__ import annotations

from pathlib import Path

import pytest

from clinical_ml_kits.testing.reference_kit import ReferenceKitChecks

KIT = Path(__file__).resolve().parents[1]
ROOT = KIT.parents[2]
CHECKS = ReferenceKitChecks(KIT, ROOT / "synthetic" / "golden" / "ckd", ROOT)


def test_cases_controls_and_non_cases() -> None:
    # eGFR, albuminuria and diagnosis routes; single abnormal value; AKI-only; dialysis exclusion;
    # valid control; inadequate history
    CHECKS.check_cohort("cohort")


def test_index_time_and_chronicity_based_index() -> None:
    CHECKS.check_case_index_visits("cohort")
    t = CHECKS.cohort_from_golden("cohort").table.set_index("person_id")
    # two low values 50 days apart (2023-01-10, 2023-03-01) are not yet chronic; the index is the
    # third value on 2023-05-01, 111 days after the first
    assert str(t.loc["SYN-CKD-CASE", "index_time"].date()) == "2023-05-01"


def test_inadequate_history_control_rejected() -> None:
    r = CHECKS.cohort_from_golden("cohort")
    assert "SYN-CKD-SHORTHIST" not in set(r.table.person_id)
    assert r.counts["excluded_min_history"] >= 1


def test_target_defining_features_excluded() -> None:
    CHECKS.check_target_features_excluded()


def test_label_defining_overlap_rejected() -> None:
    CHECKS.check_label_overlap_rejected()


def test_feature_timeline_future_revealer_and_label_values_excluded() -> None:
    CHECKS.check_features("features")


def test_same_day_rule() -> None:
    CHECKS.check_same_day_rule("features", "hemoglobin__latest", 10.2)


def test_one_row_per_person_and_two_row_rejected() -> None:
    CHECKS.check_partitions()
    CHECKS.check_two_row_rejected()


def test_groups_and_grouped_cv() -> None:
    CHECKS.check_groups_cv()


def test_control_sampling_reproducible_and_prevalence_recorded() -> None:
    CHECKS.check_sampling_reproducible()


def test_envelopes() -> None:
    CHECKS.check_envelopes()


def test_provenance_and_levels() -> None:
    CHECKS.check_provenance_report()
    CHECKS.check_levels()


def test_approved_rejected_while_provisional(tmp_path: Path) -> None:
    CHECKS.check_approved_rejected(tmp_path)


@pytest.mark.notebook
def test_generated_notebook_executes() -> None:
    CHECKS.check_notebook_executes()
