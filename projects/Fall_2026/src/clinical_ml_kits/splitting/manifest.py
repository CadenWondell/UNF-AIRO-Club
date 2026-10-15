"""SplitManifest: split settings and per-partition aggregates. Never person IDs or group keys."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PartitionStats(BaseModel):
    model_config = ConfigDict(extra="forbid")
    n: int
    n_pos: int
    prevalence: float


class SplitManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy: str = "hash"
    salt: str
    salt_version: int
    kit_version: str
    fractions: tuple[float, float, float]
    digest: str
    sampled_development_prevalence: float
    partitions: dict[str, PartitionStats]
