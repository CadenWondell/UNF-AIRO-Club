"""DataEnvironmentPolicy (contracts/dataset-adapter.md).

The All of Us dissemination parameters are read only from the V-03 SourceRecord
(``definitions/sources/aou_dissemination_policy.yaml``); this module holds no threshold value.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from clinical_ml_kits.core.errors import PendingVerification, PolicyViolation
from clinical_ml_kits.provenance.models import SourceRecord

V03_SOURCE_ID = "aou_dissemination_policy"


@dataclass(frozen=True)
class DisseminationRule:
    """Small-count rule for aggregates leaving a restricted environment (V-03)."""

    source_id: str
    suppress_min: int
    suppress_max: int
    zero_permitted: bool
    derived_values_restricted: bool
    marker: str

    @classmethod
    def from_source(cls, rec: SourceRecord) -> DisseminationRule:
        if rec.verification_status != "verified" or not rec.parameters:
            raise PendingVerification("V-03", f"{rec.source_id} is not verified")
        p = rec.parameters
        try:
            return cls(
                source_id=rec.source_id,
                suppress_min=int(p["suppress_min"]),  # type: ignore[call-overload]
                suppress_max=int(p["suppress_max"]),  # type: ignore[call-overload]
                zero_permitted=bool(p["zero_permitted"]),
                derived_values_restricted=bool(p["derived_values_restricted"]),
                marker=str(p["suppressed_marker"]),
            )
        except KeyError as e:
            raise PendingVerification("V-03", f"{rec.source_id} lacks parameter {e}") from e

    def is_restricted(self, count: int) -> bool:
        if count == 0:
            return not self.zero_permitted
        return self.suppress_min <= count <= self.suppress_max


@dataclass(frozen=True)
class DataEnvironmentPolicy:
    name: str
    participant_level: bool
    serialize_in_environment: bool
    portable_artifacts: bool
    required_validation_level: str
    allow_writes_inside_checkout: bool
    dissemination_source_id: str | None

    def dissemination_rule(self, definitions_dir: Path) -> DisseminationRule | None:
        """The rule for aggregates leaving this environment (None: no rule applies).

        Raises PendingVerification("V-03") when the environment needs a rule and its verified
        SourceRecord is unavailable.
        """
        if self.dissemination_source_id is None:
            return None
        p = Path(definitions_dir) / "sources" / f"{self.dissemination_source_id}.yaml"
        if not p.is_file():
            raise PendingVerification("V-03", f"dissemination source record missing: {p}")
        rec = SourceRecord.model_validate(yaml.safe_load(p.read_text()))
        return DisseminationRule.from_source(rec)

    def check_write_path(self, path: Path) -> None:
        """Refuse writes inside a git checkout where the policy forbids them."""
        if self.allow_writes_inside_checkout:
            return
        p = Path(path).resolve()
        for parent in [p, *p.parents]:
            if (parent / ".git").exists():
                raise PolicyViolation(
                    f"{self.name}: writing {p} inside the git checkout {parent} is not permitted; "
                    "write to the workspace instead"
                )


POLICIES: dict[str, DataEnvironmentPolicy] = {
    "synthetic": DataEnvironmentPolicy(
        name="synthetic",
        participant_level=False,
        serialize_in_environment=True,
        portable_artifacts=True,
        required_validation_level="synthetic",
        allow_writes_inside_checkout=True,
        dissemination_source_id=None,
    ),
    # Public datasets: portability is license-dependent; no M1–4 kit uses one.
    "public": DataEnvironmentPolicy(
        name="public",
        participant_level=False,
        serialize_in_environment=True,
        portable_artifacts=False,
        required_validation_level="synthetic",
        allow_writes_inside_checkout=True,
        dissemination_source_id=None,
    ),
    "all_of_us_workbench": DataEnvironmentPolicy(
        name="all_of_us_workbench",
        participant_level=True,
        serialize_in_environment=True,
        portable_artifacts=False,
        required_validation_level="workbench",
        allow_writes_inside_checkout=False,
        dissemination_source_id=V03_SOURCE_ID,
    ),
}


def policy_for(environment: str) -> DataEnvironmentPolicy:
    return POLICIES[environment]
