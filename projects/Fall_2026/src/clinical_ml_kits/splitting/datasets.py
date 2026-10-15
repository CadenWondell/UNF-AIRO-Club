"""Dataset/KitData containers with masked groups and a hidden test partition."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from clinical_ml_kits.splitting import guard
from clinical_ml_kits.splitting.groups import OpaqueGroups, group_keys
from clinical_ml_kits.splitting.hash_split import split_cohort
from clinical_ml_kits.splitting.manifest import SplitManifest


@dataclass
class Dataset:
    X: pd.DataFrame
    y: pd.Series
    index_times: pd.Series
    groups: OpaqueGroups = field(repr=False)
    person_ids: pd.Series | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return (
            f"Dataset(n={len(self.X)}, features={self.X.shape[1]}, "
            f"positives={int(self.y.sum())}, groups={self.groups!r})"
        )


@dataclass
class KitData:
    train: Dataset
    validation: Dataset
    kit_id: str
    environment: str
    split_manifest: SplitManifest
    feature_spec: Any = None
    run_manifest: Any = None
    run_log: list[datetime] = field(default_factory=list)
    _token: str = field(default="", repr=False)

    def summary(self) -> pd.DataFrame:
        """Partition sizes and sampled development prevalence (test shown as aggregates only)."""
        rows = {p: s.model_dump() for p, s in self.split_manifest.partitions.items()}
        return pd.DataFrame(rows).T[["n", "n_pos", "prevalence"]]


def _dataset(table: pd.DataFrame, X: pd.DataFrame, salt: str, synthetic: bool) -> Dataset:
    ids = list(table.person_id)
    Xp = X.loc[ids].reset_index(drop=True)
    return Dataset(
        X=Xp,
        y=table.label.astype(int).reset_index(drop=True).rename("label"),
        index_times=pd.to_datetime(table.index_time).reset_index(drop=True),
        groups=group_keys(ids, salt),
        person_ids=pd.Series(ids, name="person_id") if synthetic else None,
    )


def make_kit_data(
    table: pd.DataFrame,
    X: pd.DataFrame,
    *,
    salt: str,
    fractions: tuple[float, float, float],
    environment: str,
    kit_id: str,
    salt_version: int = 1,
    kit_version: str = "0.0.0",
    min_positives: int = 1,
    tolerance: float = 1.0,
) -> KitData:
    """Split a one-row-per-person cohort and its feature matrix (indexed by person_id)."""
    part, manifest = split_cohort(
        table,
        salt=salt,
        salt_version=salt_version,
        kit_version=kit_version,
        fractions=fractions,
        min_positives=min_positives,
        tolerance=tolerance,
    )
    synthetic = environment != "all_of_us_workbench"
    t = table.assign(_p=table.person_id.map(part))
    sets = {p: _dataset(t[t._p == p], X, salt, synthetic) for p in ("train", "validation", "test")}
    token = uuid.uuid4().hex
    guard.deposit(token, sets["test"])
    return KitData(sets["train"], sets["validation"], kit_id, environment, manifest, _token=token)
