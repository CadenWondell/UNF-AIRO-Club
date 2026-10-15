"""T091: the held-out test partition is reachable only through the guard."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest

from clinical_ml_kits.splitting.datasets import make_kit_data
from clinical_ml_kits.splitting.guard import release_test

N = 400
PIDS = [f"SYN-P-{i:06d}" for i in range(N)]
X = pd.DataFrame({"a": np.arange(N, dtype=float)}, index=PIDS)
TABLE = pd.DataFrame(
    {
        "person_id": PIDS,
        "label": [i % 3 == 0 for i in range(N)],
        "index_time": pd.Timestamp("2025-01-01"),
    }
).astype({"label": int})


def _deep_values(obj: object, depth: int = 0) -> list[object]:
    if depth > 3:
        return []
    out: list[object] = []
    for v in getattr(obj, "__dict__", {}).values():
        out.append(v)
        out += _deep_values(v, depth + 1)
    return out


def test_kitdata_exposes_no_test_rows() -> None:
    data = make_kit_data(
        TABLE, X, salt="g-s1", fractions=(0.6, 0.2, 0.2), environment="synthetic", kit_id="g"
    )
    assert not hasattr(data, "test")
    from clinical_ml_kits.splitting.hash_split import assign_partitions

    part = assign_partitions(PIDS, "g-s1", (0.6, 0.2, 0.2))
    test_ids = set(part[part == "test"].index)
    assert len(test_ids) == data.split_manifest.partitions["test"].n > 0
    visible = set(data.train.person_ids) | set(data.validation.person_ids)  # type: ignore[arg-type]
    assert len(visible) == N - len(test_ids) and not (visible & test_ids)
    test_x = set(X.loc[sorted(test_ids)].a)
    for v in _deep_values(data):
        if isinstance(v, pd.Series) and v.name == "person_id":
            assert not (set(v) & test_ids)
        if isinstance(v, pd.DataFrame) and "a" in v:
            assert not (set(v.a) & test_x)


def test_guard_logs_and_warns_on_repeat(caplog: pytest.LogCaptureFixture) -> None:
    data = make_kit_data(
        TABLE, X, salt="g-s1", fractions=(0.6, 0.2, 0.2), environment="synthetic", kit_id="g"
    )
    with caplog.at_level(logging.INFO, logger="clinical_ml_kits"):
        test = release_test(data)
    assert len(test.X) == data.split_manifest.partitions["test"].n
    assert len(test.groups) == len(test.X)
    assert [r for r in caplog.records if getattr(r, "ckit_event", "") == "final_test_access"]
    assert len(data.run_log) == 1
    with pytest.warns(UserWarning, match="again"):
        release_test(data)
    assert len(data.run_log) == 2
