"""Kit catalog (``kits/catalog.yaml``): candidate statuses with recorded decisions (FR-080)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

STATUSES = ("candidate", "approved", "revised", "merged", "postponed", "replaced", "rejected")
CatalogStatus = Literal[
    "candidate", "approved", "revised", "merged", "postponed", "replaced", "rejected"
]


class CatalogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    dataset: str
    status: CatalogStatus
    reference: bool = False
    decision_rationale: str = ""
    evaluation: str | None = None
    decided_on: date | None = None
    reviewer: str | None = None
    # Kit verification state while still a candidate (e.g., requires_verification) and the
    # open verification items blocking approval.
    verification_state: Literal["requires_verification", "verified"] | None = None
    blockers: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _decision_recorded(self) -> CatalogEntry:
        if self.status != "candidate":
            missing = [
                k for k in ("decision_rationale", "decided_on", "reviewer") if not getattr(self, k)
            ]
            if missing:
                raise ValueError(f"status {self.status} requires {', '.join(missing)}")
        if self.status == "approved" and not self.evaluation:
            raise ValueError("status approved requires an evaluation (FR-081 evidence link)")
        return self


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    catalog_version: int
    entries: list[CatalogEntry]

    @model_validator(mode="after")
    def _unique(self) -> Catalog:
        ids = [e.candidate_id for e in self.entries]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"duplicate candidate_id {dupes}")
        return self

    @classmethod
    def load(cls, path: Path) -> Catalog:
        return cls.model_validate(yaml.safe_load(Path(path).read_text()))

    def get(self, candidate_id: str) -> CatalogEntry | None:
        return next((e for e in self.entries if e.candidate_id == candidate_id), None)
