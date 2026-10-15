"""FR-081 data-availability evidence record (``kits/<dataset>/<kit>/evidence/fr081.yaml``).

Only aggregates permitted by the V-03 dissemination rule may be written here; values that the
rule suppresses are recorded as the string ``"<=20"`` (see completion/suppression.py).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

Count = int | str  # an integer count, or a suppressed marker such as "<=20"


class FeatureCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature: str
    coverage: float | str  # fraction of eligible persons with ≥1 value, or suppressed marker
    missingness: float | str


class FR081Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kit_id: str
    cdr_version: str
    run_date: date
    checklist_reference: str
    eligible_persons: Count
    positives: Count
    eligible_controls: Count
    class_balance: float | str
    required_feature_availability: list[FeatureCoverage] = Field(default_factory=list)
    longitudinal_coverage: str | None = None
    dissemination_rule: str = Field(description="SourceRecord id of the V-03 rule applied")
    notes: str = ""
