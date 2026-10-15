"""T025: kit-definition schema, value states, and validation levels."""

from __future__ import annotations

from pathlib import Path

import pytest

from clinical_ml_kits.core.errors import KitValidationError
from clinical_ml_kits.core.kit_schema import (
    LEVELS,
    Provisional,
    Unverified,
    ValidationContext,
    load_kit_definition,
    validate_kit,
)

FIX = Path(__file__).resolve().parents[2] / "fixtures"
CTX = ValidationContext.from_root(FIX)

# fixture name -> (offending field fragment, level at which it must fail)
INVALID = {
    "bad_prediction_type": ("prediction_type", "schema"),
    "current_state_with_horizon": ("horizon", "schema"),
    "future_risk_without_horizon": ("horizon", "schema"),
    "missing_phenotype_version": ("phenotype.version", "schema"),
    "missing_dataset_version": ("dataset.version", "schema"),
    "invalid_status": ("status", "schema"),
    "approved_unverified_ref": ("status", "schema"),
    "approved_with_provisional": ("status", "schema"),
    "provisional_missing_note": ("temporal_policy.same_day", "schema"),
    "provisional_missing_pending": ("temporal_policy.washout", "schema"),
    "feature_also_prohibited": ("prohibited", "schema"),
    "same_day_absent": ("temporal_policy.same_day", "schema"),
    "unverified_at_synthetic": ("temporal_policy.washout", "synthetic"),
    "provisional_at_workbench": ("temporal_policy.same_day", "workbench"),
    "metrics_not_imbalance_aware": ("metrics", "schema"),
    "unknown_template_family": ("template_family", "schema"),
    "control_sampling_missing": ("phenotype.control_sampling", "schema"),
    "random_ratio_without_ratio": ("control_sampling.controls_per_case", "schema"),
    "matched_without_match_on": ("control_sampling.match_on", "schema"),
    "salt_changed_without_bump": ("split.salt_history", "schema"),
    "namespace_concept_ref": ("label_defining_concepts", "schema"),
    "grouped_native_unverified": ("calibration.method", "schema"),
    "synthetic_population_missing": ("synthetic_population", "synthetic"),
}


def test_one_invalid_fixture_per_case() -> None:
    names = {p.stem for p in (FIX / "kits" / "invalid").glob("*.yaml")}
    assert names == set(INVALID)


@pytest.mark.parametrize("name", sorted(INVALID))
def test_invalid_fixture_names_field_and_level(name: str) -> None:
    field, fail_level = INVALID[name]
    path = FIX / "kits" / "invalid" / f"{name}.yaml"
    levels_before = LEVELS[: LEVELS.index(fail_level)]
    for level in levels_before:
        validate_kit(load_kit_definition(path), level, CTX)
    with pytest.raises(KitValidationError) as exc:
        validate_kit(load_kit_definition(path), fail_level, CTX)
    msg = str(exc.value)
    assert field in msg, msg
    if fail_level != "schema":
        assert fail_level in msg


def test_grouped_native_reports_pending_v14() -> None:
    path = FIX / "kits" / "invalid" / "grouped_native_unverified.yaml"
    with pytest.raises(KitValidationError, match="V-14"):
        validate_kit(load_kit_definition(path), "schema", CTX)


def test_provisional_fixture_levels() -> None:
    kit = load_kit_definition(FIX / "kits" / "valid" / "provisional_kit.yaml")
    validate_kit(kit, "schema", CTX)
    validate_kit(kit, "synthetic", CTX)
    for level in ("workbench", "approval"):
        with pytest.raises(KitValidationError) as exc:
            validate_kit(kit, level, CTX)
        msg = str(exc.value)
        # every provisional item is listed
        for item in (
            "temporal_policy.same_day",
            "temporal_policy.exclude_index_encounter",
            "temporal_policy.washout",
            "temporal_policy.lookback",
            "phenotype.min_observation_history",
            "phenotype.control_sampling.controls_per_case",
        ):
            assert item in msg, (level, item)


def test_verified_fixture_passes_all_levels() -> None:
    kit = load_kit_definition(FIX / "kits" / "valid" / "verified_kit" / "kit.yaml")
    for level in LEVELS:
        validate_kit(kit, level, CTX)


def test_value_states_parse() -> None:
    kit = load_kit_definition(FIX / "kits" / "valid" / "provisional_kit.yaml")
    same_day = kit.definition.temporal_policy.same_day
    assert isinstance(same_day, Provisional)
    assert same_day.provisional == "exclude_index_day" and same_day.pending == "V-20"
    assert isinstance(kit.definition.dataset.version, Unverified)


def test_temporal_policy_has_no_defaults() -> None:
    from clinical_ml_kits.core.kit_schema import TemporalPolicy

    for f in ("same_day", "exclude_index_encounter"):
        assert TemporalPolicy.model_fields[f].is_required()


def test_provisional_note_must_disclaim() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="note"):
        Provisional[int].model_validate({"provisional": 2, "note": "two", "pending": "V-21"})
