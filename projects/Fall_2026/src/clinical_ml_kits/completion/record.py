"""CompletionRecord: the deliverable of a completed model in any environment (FR-095)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CompletionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: str
    model_version: str
    kit_id: str
    kit_definition_hash: str
    phenotype_version: str
    environment: str
    metrics: dict[str, Any]
    calibration: dict[str, Any] = Field(default_factory=dict)
    explainability: dict[str, Any] = Field(default_factory=dict)
    run_manifest: dict[str, Any]
    run_manifest_hash: str
    portable: bool = False
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    disclaimer: str = (
        "Educational/research output. Not a clinically validated risk score, diagnosis, or "
        "treatment recommendation."
    )

    def export(self, policy: Any, definitions_dir: Path) -> dict[str, Any]:
        """JSON-ready dict for leaving the environment: V-03 filter applied when required."""
        data = self.model_dump(mode="json")
        rule = policy.dissemination_rule(definitions_dir)
        if rule is None:
            return data
        from clinical_ml_kits.completion.suppression import filter_for_export

        out: dict[str, Any] = filter_for_export(data, rule)
        out["dissemination_rule"] = rule.source_id
        return out
