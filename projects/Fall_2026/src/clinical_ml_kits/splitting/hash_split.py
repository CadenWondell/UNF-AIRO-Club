"""Deterministic hash-based patient split (research R-10)."""

from __future__ import annotations

import hashlib
import warnings
from collections.abc import Sequence

import numpy as np
import pandas as pd

from clinical_ml_kits.core.errors import KitValidationError
from clinical_ml_kits.splitting.manifest import PartitionStats, SplitManifest

PARTITIONS = ("train", "validation", "test")


def _unit(salt: str, person_id: str) -> float:
    h = hashlib.sha256(f"{salt}{person_id}".encode()).hexdigest()
    return int(h[:15], 16) / 16**15


def assign_partitions(
    person_ids: Sequence[str], salt: str, fractions: Sequence[float]
) -> pd.Series:
    """Partition per person from SHA-256(salt + person_id). Takes no outcome information."""
    ids = pd.Index(list(person_ids), name="person_id")
    u = np.array([_unit(salt, str(p)) for p in ids])
    edges = np.cumsum(fractions)[:-1]
    labels = np.array(PARTITIONS, dtype=object)[np.searchsorted(edges, u, side="right")]
    return pd.Series(labels, index=ids, name="partition")


def split_cohort(
    table: pd.DataFrame,
    *,
    salt: str,
    salt_version: int,
    kit_version: str,
    fractions: Sequence[float],
    min_positives: int,
    tolerance: float,
) -> tuple[pd.Series, SplitManifest]:
    """Split a one-row-per-person ``table`` (person_id, label); validate positives/prevalence."""
    part = assign_partitions(table.person_id, salt, fractions)
    labels = table.set_index("person_id").label
    overall = float(labels.mean())
    stats: dict[str, PartitionStats] = {}
    for p in PARTITIONS:
        y = labels[part == p]
        stats[p] = PartitionStats(
            n=len(y), n_pos=int(y.sum()), prevalence=float(y.mean()) if len(y) else float("nan")
        )
    short = [p for p in PARTITIONS if stats[p].n_pos < min_positives]
    if short:
        raise KitValidationError(
            "split.min_positives_per_partition",
            f"partitions {short} have fewer than {min_positives} positives "
            f"({ {p: stats[p].n_pos for p in short} }); revisit the cohort or fractions as a "
            "documented method decision — never try other salts",
        )
    for p in PARTITIONS:
        if abs(stats[p].prevalence - overall) > tolerance:
            warnings.warn(
                f"{p} prevalence {stats[p].prevalence:.3f} deviates from overall {overall:.3f} "
                f"by more than {tolerance}",
                UserWarning,
                stacklevel=2,
            )
    digest = hashlib.sha256(
        "\n".join(f"{i}\t{v}" for i, v in sorted(part.items())).encode()
    ).hexdigest()
    manifest = SplitManifest(
        salt=salt,
        salt_version=salt_version,
        kit_version=kit_version,
        fractions=tuple(fractions),
        digest=digest,
        sampled_development_prevalence=overall,
        partitions=stats,
    )
    return part, manifest
