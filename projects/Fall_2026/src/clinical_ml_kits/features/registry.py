"""Feature registry (``definitions/features/registry.yaml``): semantic keys → logical concepts."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field

from clinical_ml_kits.core.values import ClinicalValue, resolve, state_of
from clinical_ml_kits.features.concept_sets import SEMVER, Domain, LogicalConceptRef
from clinical_ml_kits.provenance.models import ProvenanceRef

ValueType = Literal["numeric", "categorical", "boolean", "event"]


class FeatureRegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    feature_key: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=1)
    domain: Domain
    value_type: ValueType
    concept: LogicalConceptRef
    canonical_unit: ClinicalValue[str] | None = None
    plausible_range: ClinicalValue[tuple[float, float]] | None = None
    status: Literal["draft", "requires_verification", "verified", "approved"]
    provenance: list[ProvenanceRef] = Field(min_length=1)


class FeatureRegistry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registry_version: str = Field(pattern=SEMVER)
    features: list[FeatureRegistryEntry]

    @classmethod
    def load(cls, path: Path) -> FeatureRegistry:
        reg = cls.model_validate(yaml.safe_load(Path(path).read_text()))
        keys = [f.feature_key for f in reg.features]
        dupes = {k for k in keys if keys.count(k) > 1}
        if dupes:
            raise ValueError(f"duplicate feature keys: {sorted(dupes)}")
        return reg

    def get(self, key: str) -> FeatureRegistryEntry:
        for f in self.features:
            if f.feature_key == key:
                return f
        raise KeyError(f"feature {key!r} is not in the feature registry")

    def resolve(self, key: str, adapter: Any) -> Any:
        """The active adapter's realization for a feature's logical concept (may raise)."""
        return adapter.resolve(self.get(key).concept.id)

    def __contains__(self, key: object) -> bool:
        return any(f.feature_key == key for f in self.features)


def flag_out_of_range(
    obs: pd.DataFrame, registry: FeatureRegistry, concept_to_feature: dict[str, str]
) -> pd.DataFrame:
    """Add ``out_of_range`` (bool) using provisional/verified plausible ranges; never clamps.

    Ranges that are UNVERIFIED (or absent) flag nothing.
    """
    out = obs.copy()
    out["out_of_range"] = False
    for concept, key in concept_to_feature.items():
        if key not in registry:
            continue
        rng = registry.get(key).plausible_range
        if rng is None or state_of(rng) == "unverified":
            continue
        lo, hi = resolve(rng)
        sel = out.logical_concept == concept
        v = out.loc[sel, "value_num"]
        out.loc[sel, "out_of_range"] = ((v < lo) | (v > hi)).fillna(False).to_numpy()
    return out
