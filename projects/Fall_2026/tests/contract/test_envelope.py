"""T027: prediction envelope contract v1.0.0 (contracts/prediction-envelope.md)."""

from __future__ import annotations

import copy
from typing import Any

import pytest
from pydantic import ValidationError

from clinical_ml_kits.prediction.envelope import (
    CONTRACT_VERSION,
    DISCLAIMER,
    PredictionEnvelope,
)

EXAMPLE: dict[str, Any] = {
    "contract_version": "1.0.0",
    "kit_id": "aou_t2d_current",
    "model_id": "aou_t2d_current.baseline_lr",
    "model_version": "0.1.0",
    "target": {"code": "t2d_phenotype", "label": "Type 2 diabetes phenotype"},
    "prediction_type": "current_state",
    "as_of": "2026-01-01T00:00:00+00:00",
    "horizon": None,
    "dataset": {"id": "synthetic_clinical", "version": "0.1.0"},
    "definition_versions": {
        "phenotype": "0.1.0",
        "cohort": "0.1.0",
        "kit": "0.1.0",
        "feature_registry": "0.1.0",
    },
    "data_environment": "synthetic",
    "subject_ref": "SYN-000042",
    "payload": {
        "payload_type": "binary_probability",
        "probability": 0.31,
        "threshold": 0.27,
        "predicted_class": 1,
        "probability_basis": "development_sample",
    },
    "calibration_status": "assessed",
    "disclaimer": DISCLAIMER,
}

REQUIRED = [
    "contract_version",
    "kit_id",
    "model_id",
    "model_version",
    "target",
    "prediction_type",
    "as_of",
    "dataset",
    "definition_versions",
    "data_environment",
    "subject_ref",
    "payload",
    "disclaimer",
]


def _env(**over: Any) -> dict[str, Any]:
    d = copy.deepcopy(EXAMPLE)
    d.update(over)
    return d


def test_example_is_valid() -> None:
    env = PredictionEnvelope.model_validate(EXAMPLE)
    assert env.contract_version == CONTRACT_VERSION == "1.0.0"


@pytest.mark.parametrize("field", REQUIRED)
def test_required_fields(field: str) -> None:
    d = _env()
    del d[field]
    with pytest.raises(ValidationError, match=field):
        PredictionEnvelope.model_validate(d)


def test_horizon_null_iff_current_state() -> None:
    with pytest.raises(ValidationError, match="horizon"):
        PredictionEnvelope.model_validate(_env(horizon="P365D"))
    with pytest.raises(ValidationError, match="horizon"):
        PredictionEnvelope.model_validate(_env(prediction_type="future_risk", horizon=None))
    PredictionEnvelope.model_validate(_env(prediction_type="future_risk", horizon="P365D"))


@pytest.mark.parametrize("p", [-0.01, 1.01])
def test_probability_range(p: float) -> None:
    d = _env()
    d["payload"]["probability"] = p
    with pytest.raises(ValidationError, match="probability"):
        PredictionEnvelope.model_validate(d)


def test_predicted_class_consistent_with_threshold() -> None:
    d = _env()
    d["payload"]["predicted_class"] = 0  # 0.31 >= 0.27 => must be 1
    with pytest.raises(ValidationError, match="predicted_class"):
        PredictionEnvelope.model_validate(d)
    d["payload"]["predicted_class"] = None
    PredictionEnvelope.model_validate(d)


def test_probability_basis_required_and_restricted() -> None:
    d = _env()
    del d["payload"]["probability_basis"]
    with pytest.raises(ValidationError, match="probability_basis"):
        PredictionEnvelope.model_validate(d)
    d["payload"]["probability_basis"] = "population"
    with pytest.raises(ValidationError, match="probability_basis"):
        PredictionEnvelope.model_validate(d)


def test_disclaimer_constant() -> None:
    with pytest.raises(ValidationError, match="disclaimer"):
        PredictionEnvelope.model_validate(_env(disclaimer="Clinically validated!"))


def test_unknown_payload_type_rejected() -> None:
    d = _env()
    d["payload"] = {"payload_type": "segmentation", "mask": "x"}
    with pytest.raises(ValidationError):
        PredictionEnvelope.model_validate(d)


def test_no_person_id_or_group_key_anywhere() -> None:
    with pytest.raises(ValidationError):
        PredictionEnvelope.model_validate(_env(person_id="123"))
    with pytest.raises(ValidationError):
        PredictionEnvelope.model_validate(_env(groups="abc"))
    d = _env()
    d["input_metadata"] = {"features_present": 3, "features_missing": [], "group": "g"}
    with pytest.raises(ValidationError):
        PredictionEnvelope.model_validate(d)
    # Opaque group-key-shaped subject references are rejected.
    with pytest.raises(ValidationError, match="subject_ref"):
        PredictionEnvelope.model_validate(_env(subject_ref="group:abcdef0123456789"))


def test_workbench_subject_ref_not_synthetic_only_check() -> None:
    # Outside the Workbench, subject_ref must be a synthetic/demo identifier.
    with pytest.raises(ValidationError, match="subject_ref"):
        PredictionEnvelope.model_validate(_env(subject_ref="1234567"))


def test_json_round_trip() -> None:
    env = PredictionEnvelope.model_validate(EXAMPLE)
    again = PredictionEnvelope.model_validate_json(env.model_dump_json())
    assert again == env
