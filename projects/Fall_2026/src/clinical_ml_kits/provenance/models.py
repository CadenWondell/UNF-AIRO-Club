"""Provenance models: SourceRecord, ProvenanceRef, Deviation (data-model § 2)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VerificationStatus = Literal["draft", "requires_verification", "verified"]


class SourceRecord(BaseModel):
    """One documented source (``definitions/sources/<source_id>.yaml``)."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_\-]*$")
    title: str = Field(min_length=1)
    organization: str = Field(min_length=1)
    url_or_identifier: str = Field(min_length=1)
    source_version: str | None = None
    accessed_date: date | None = None
    priority_tier: int = Field(ge=1, le=6)
    notes: str = ""
    # Structured, machine-readable findings (e.g., the V-03 dissemination parameters).
    parameters: dict[str, object] | None = None
    verification_status: VerificationStatus = "requires_verification"
    verified_by: str | None = None
    verified_on: date | None = None

    @model_validator(mode="after")
    def _verified_needs_verifier(self) -> SourceRecord:
        if self.verification_status == "verified":
            if not self.verified_by:
                raise ValueError("verified_by is required when verification_status is verified")
            if not self.verified_on:
                raise ValueError("verified_on is required when verification_status is verified")
        return self


class ProvenanceRef(BaseModel):
    """Inline provenance attached to the item it supports."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    locator: str = Field(min_length=1)
    application: str = Field(min_length=1)
    verification_status: VerificationStatus
    verified_by: str | None = None
    verified_on: date | None = None
    content_hash: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def _verified_needs_verifier(self) -> ProvenanceRef:
        if self.verification_status == "verified":
            if not self.verified_by:
                raise ValueError("verified_by is required when verification_status is verified")
            if not self.verified_on:
                raise ValueError("verified_on is required when verification_status is verified")
        return self

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "verified"


class Deviation(BaseModel):
    """An intentional deviation from an official definition (FR-157)."""

    model_config = ConfigDict(extra="forbid")

    item: str = Field(min_length=1)
    official_definition: str = Field(min_length=1)
    deviation: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    expected_impact: str = Field(min_length=1)
