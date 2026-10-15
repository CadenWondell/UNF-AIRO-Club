"""T086: deterministic patient-level hash split and split manifest."""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from clinical_ml_kits.core.errors import KitValidationError
from clinical_ml_kits.splitting.hash_split import assign_partitions, split_cohort

PIDS = [f"SYN-P-{i:06d}" for i in range(2000)]
FR = (0.7, 0.15, 0.15)


def _table(n: int = 2000, prev: float = 0.3, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"person_id": PIDS[:n], "label": (rng.random(n) < prev).astype(int)})


def test_deterministic_and_salt_dependent() -> None:
    a, b = assign_partitions(PIDS, "k-s1", FR), assign_partitions(PIDS, "k-s1", FR)
    pd.testing.assert_series_equal(a, b)
    assert not a.equals(assign_partitions(PIDS, "k-s2", FR))
    assert set(a) == {"train", "validation", "test"}
    assert abs((a == "train").mean() - 0.7) < 0.04


def test_each_person_exactly_one_partition_and_rows_share() -> None:
    rows = pd.DataFrame({"person_id": PIDS[:50] * 3})  # three rows per person
    part = rows.person_id.map(assign_partitions(PIDS[:50], "k-s1", FR))
    assert rows.assign(p=part).groupby("person_id").p.nunique().eq(1).all()


def test_adding_persons_never_moves_existing() -> None:
    small = assign_partitions(PIDS[:1000], "k-s1", FR)
    big = assign_partitions(PIDS, "k-s1", FR)
    pd.testing.assert_series_equal(small, big.loc[small.index])


def test_assignment_ignores_outcome() -> None:
    assert list(inspect.signature(assign_partitions).parameters) == [
        "person_ids",
        "salt",
        "fractions",
    ]
    t = _table()
    a1, _ = split_cohort(
        t,
        salt="k-s1",
        salt_version=1,
        kit_version="0.1.0",
        fractions=FR,
        min_positives=10,
        tolerance=0.2,
    )
    t2 = t.assign(label=np.random.default_rng(9).permutation(t.label))
    a2, _ = split_cohort(
        t2,
        salt="k-s1",
        salt_version=1,
        kit_version="0.1.0",
        fractions=FR,
        min_positives=10,
        tolerance=0.2,
    )
    pd.testing.assert_series_equal(a1, a2)


def test_no_person_crosses_partitions() -> None:
    a, _ = split_cohort(
        _table(),
        salt="k-s1",
        salt_version=1,
        kit_version="0.1.0",
        fractions=FR,
        min_positives=10,
        tolerance=0.2,
    )
    parts = {p: set(a[a == p].index) for p in ("train", "validation", "test")}
    assert not (parts["train"] & parts["validation"]) and not (parts["train"] & parts["test"])
    assert not (parts["validation"] & parts["test"])


def test_min_positives_raises() -> None:
    with pytest.raises(KitValidationError, match="min_positives_per_partition"):
        split_cohort(
            _table(n=200, prev=0.05),
            salt="k-s1",
            salt_version=1,
            kit_version="0.1.0",
            fractions=FR,
            min_positives=10,
            tolerance=0.5,
        )


def test_prevalence_tolerance_warns() -> None:
    with pytest.warns(UserWarning, match="prevalence"):
        split_cohort(
            _table(n=300, prev=0.4),
            salt="k-s1",
            salt_version=1,
            kit_version="0.1.0",
            fractions=FR,
            min_positives=1,
            tolerance=0.0001,
        )


def test_manifest_contents_without_person_ids() -> None:
    a, m = split_cohort(
        _table(),
        salt="k-s1",
        salt_version=1,
        kit_version="0.1.0",
        fractions=FR,
        min_positives=10,
        tolerance=0.2,
    )
    assert (m.salt, m.salt_version, m.kit_version) == ("k-s1", 1, "0.1.0")
    assert set(m.partitions) == {"train", "validation", "test"}
    assert m.partitions["train"].n == int((a == "train").sum())
    assert 0 < m.sampled_development_prevalence < 1 and len(m.digest) == 64
    dumped = m.model_dump_json()
    assert "SYN-P-" not in dumped
