"""T018: framework logger namespace and structured event helpers."""

from __future__ import annotations

import logging

import pytest

from clinical_ml_kits.core import logging as ckit_logging

EVENTS = {
    "final_test_access": ckit_logging.log_final_test_access,
    "environment_selected": ckit_logging.log_environment_selected,
    "model_completed": ckit_logging.log_model_completed,
    "validation_failed": ckit_logging.log_validation_failed,
}


def test_logger_namespace() -> None:
    assert ckit_logging.get_logger().name == "clinical_ml_kits"
    assert ckit_logging.get_logger("cohort").name == "clinical_ml_kits.cohort"


@pytest.mark.parametrize("event", sorted(EVENTS))
def test_event_helpers_emit_structured_records(
    event: str, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG, logger="clinical_ml_kits"):
        EVENTS[event](kit_id="toy_binary", environment="synthetic")
    records = [r for r in caplog.records if getattr(r, "ckit_event", None) == event]
    assert len(records) == 1
    rec = records[0]
    assert rec.name.startswith("clinical_ml_kits")
    assert rec.kit_id == "toy_binary"  # type: ignore[attr-defined]
    assert rec.environment == "synthetic"  # type: ignore[attr-defined]
    assert rec.timestamp  # type: ignore[attr-defined]


def test_extra_fields_are_passed_through(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, logger="clinical_ml_kits"):
        ckit_logging.log_validation_failed(kit_id="k", environment="synthetic", detail="bad field")
    (rec,) = [r for r in caplog.records if getattr(r, "ckit_event", None)]
    assert rec.detail == "bad field"  # type: ignore[attr-defined]


def test_error_hierarchy() -> None:
    from clinical_ml_kits.core import errors

    assert issubclass(errors.ProhibitedFeatureError, errors.LeakageError)
    for name in (
        "PatientLeakageError",
        "TemporalLeakageError",
        "TargetLeakageError",
        "LabelLeakageError",
        "SameDayLeakageError",
        "PreprocessingLeakageError",
    ):
        assert issubclass(getattr(errors, name), errors.LeakageError)
    err = errors.PendingVerification("V-03")
    assert err.item_id == "V-03" and "V-03" in str(err)
    kv = errors.KitValidationError("temporal_policy.same_day", "required", level="synthetic")
    assert "temporal_policy.same_day" in str(kv) and "synthetic" in str(kv)
