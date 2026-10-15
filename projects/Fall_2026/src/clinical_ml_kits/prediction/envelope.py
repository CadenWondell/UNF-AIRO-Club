"""Prediction envelope v1.0.0 (contracts/prediction-envelope.md; spec FR-090–FR-094).

M1–4 define only the ``binary_probability`` payload. Reserved payload types (survival,
segmentation, detection, signal, multiclass) are intentionally not defined, so v1.0 validators
reject them.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

CONTRACT_VERSION = "1.0.0"
DISCLAIMER = (
    "Educational/research output. Not a clinically validated risk score, diagnosis, or "
    "treatment recommendation."
)
_STRICT = ConfigDict(extra="forbid")
_GROUP_LIKE = re.compile(r"^(group:.*|[0-9a-f]{16,})$")


class TargetRef(BaseModel):
    model_config = _STRICT
    code: str = Field(min_length=1)
    label: str = Field(min_length=1)


class DatasetIdentity(BaseModel):
    model_config = _STRICT
    id: str = Field(min_length=1)
    version: str = Field(min_length=1)


class DefinitionVersions(BaseModel):
    model_config = _STRICT
    phenotype: str
    cohort: str
    kit: str
    feature_registry: str


class BinaryProbability(BaseModel):
    model_config = _STRICT
    payload_type: Literal["binary_probability"]
    probability: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    predicted_class: Literal[0, 1] | None = None
    # M1–4: the probability reflects the kit's sampled development prevalence (R-25).
    probability_basis: Literal["development_sample"]

    @model_validator(mode="after")
    def _class_consistent(self) -> BinaryProbability:
        if self.predicted_class is not None:
            expected = int(self.probability >= self.threshold)
            if self.predicted_class != expected:
                raise ValueError(
                    f"predicted_class {self.predicted_class} inconsistent with probability "
                    f"{self.probability} and threshold {self.threshold}"
                )
        return self


class Contribution(BaseModel):
    model_config = _STRICT
    feature: str
    contribution: float
    value: float | str | None = None


class Explanation(BaseModel):
    model_config = _STRICT
    method: str
    top_features: list[Contribution]


class InputMetadata(BaseModel):
    model_config = _STRICT
    features_present: int = Field(ge=0)
    features_missing: list[str] = Field(default_factory=list)


class ModelMetadata(BaseModel):
    model_config = _STRICT
    template_family: str
    trained_on_environment: Literal["synthetic", "public", "all_of_us_workbench"]
    run_manifest_hash: str
    created_at: datetime


class PredictionEnvelope(BaseModel):
    """One prediction for one subject at one as-of time from one model."""

    model_config = _STRICT

    contract_version: Literal["1.0.0"]
    kit_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    target: TargetRef
    prediction_type: Literal["current_state", "future_risk"]
    as_of: AwareDatetime
    horizon: str | None = Field(default=None, pattern=r"^P(T?\d+[YMWDHMS])+$")
    dataset: DatasetIdentity
    definition_versions: DefinitionVersions
    data_environment: Literal["synthetic", "public", "all_of_us_workbench"]
    subject_ref: str = Field(min_length=1)
    payload: BinaryProbability = Field(discriminator="payload_type")
    calibration_status: Literal["not_assessed", "assessed", "recalibrated"] | None = None
    explanation: Explanation | None = None
    input_metadata: InputMetadata | None = None
    model_metadata: ModelMetadata | None = None
    disclaimer: Literal[
        "Educational/research output. Not a clinically validated risk score, diagnosis, or "
        "treatment recommendation."
    ]

    @field_validator("subject_ref")
    @classmethod
    def _opaque_ref(cls, v: str) -> str:
        if _GROUP_LIKE.match(v):
            raise ValueError("subject_ref must not be a patient group key")
        return v

    @model_validator(mode="after")
    def _rules(self) -> PredictionEnvelope:
        if self.prediction_type == "current_state" and self.horizon is not None:
            raise ValueError("horizon must be null for current_state")
        if self.prediction_type == "future_risk" and self.horizon is None:
            raise ValueError("horizon is required for future_risk")
        if self.data_environment != "all_of_us_workbench" and not re.match(
            r"^(SYN|DEMO)-", self.subject_ref
        ):
            raise ValueError(
                "subject_ref outside the Workbench must be a synthetic/demo identifier (SYN-/DEMO-)"
            )
        return self
