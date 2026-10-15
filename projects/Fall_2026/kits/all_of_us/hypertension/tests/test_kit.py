"""T165: kit-specific tests for aou_htn_current (golden patients + synthetic population)."""

from __future__ import annotations

from pathlib import Path

import pytest

from clinical_ml_kits.testing.reference_kit import ReferenceKitChecks

KIT = Path(__file__).resolve().parents[1]
ROOT = KIT.parents[2]
CHECKS = ReferenceKitChecks(KIT, ROOT / "synthetic" / "golden" / "htn", ROOT)


def test_cases_controls_and_non_cases() -> None:
    # BP and diagnosis+medication routes; single elevated reading; pregnancy exclusion; valid
    # control; inadequate history
    CHECKS.check_cohort("cohort")


def test_index_time() -> None:
    CHECKS.check_case_index_visits("cohort")


def test_medication_with_other_indication_is_not_a_case() -> None:
    t = CHECKS.cohort_from_golden("cohort").table
    # beta-blocker for atrial fibrillation without hypertension evidence: neither case nor control
    assert "SYN-HTN-AF-BETABLOCKER" not in set(t.person_id)


def test_inadequate_history_control_rejected() -> None:
    r = CHECKS.cohort_from_golden("cohort")
    assert "SYN-HTN-SHORTHIST" not in set(r.table.person_id)
    assert r.counts["excluded_min_history"] >= 1


def test_target_defining_features_excluded() -> None:
    CHECKS.check_target_features_excluded()


def test_label_defining_overlap_rejected() -> None:
    CHECKS.check_label_overlap_rejected()


def test_feature_timeline_future_revealer_and_label_values_excluded() -> None:
    CHECKS.check_features("features")


def test_same_day_rule() -> None:
    CHECKS.check_same_day_rule("features", "heart_rate__latest", 88.0)


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
