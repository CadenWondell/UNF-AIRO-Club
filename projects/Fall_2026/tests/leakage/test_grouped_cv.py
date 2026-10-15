"""T089: opaque patient groups, grouped CV splitter, grouped calibration (V-14 pattern)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, GroupKFold, StratifiedGroupKFold

from clinical_ml_kits.evaluation.grouped_calibration import calibrate_grouped
from clinical_ml_kits.splitting.cv import make_cv_splitter
from clinical_ml_kits.splitting.datasets import make_kit_data
from clinical_ml_kits.splitting.groups import OpaqueGroups, group_keys

RNG = np.random.default_rng(0)
N = 600
PIDS = [f"SYN-P-{i:06d}" for i in range(N)]
X = pd.DataFrame({"a": RNG.normal(size=N), "b": RNG.normal(size=N)}, index=PIDS)
Y = pd.Series((X.a + RNG.normal(size=N) > 0.5).astype(int), index=PIDS)
TABLE = pd.DataFrame(
    {"person_id": PIDS, "label": Y.values, "index_time": pd.Timestamp("2025-01-01")}
)


@pytest.fixture(params=["synthetic", "all_of_us_workbench"])
def data(request: pytest.FixtureRequest):  # type: ignore[no-untyped-def]
    return make_kit_data(
        TABLE, X, salt="t-s1", fractions=(0.7, 0.15, 0.15), environment=request.param, kit_id="t"
    )


def test_groups_in_every_mode(data) -> None:  # type: ignore[no-untyped-def]
    for ds in (data.train, data.validation):
        assert isinstance(ds.groups, OpaqueGroups) and len(ds.groups) == len(ds.X)
        assert "groups" not in ds.X.columns and not any("group" in c for c in ds.X.columns)
        assert "group:" not in repr(ds) and "masked" in repr(ds.groups)
        assert ds.groups[0] not in repr(ds)


def test_person_ids_only_in_synthetic(data) -> None:  # type: ignore[no-untyped-def]
    if data.environment == "synthetic":
        assert data.train.person_ids is not None
    else:
        assert data.train.person_ids is None


def test_group_keys_shared_within_and_distinct_across() -> None:
    g = group_keys(["A", "A", "B"], "s-s1")
    assert g[0] == g[1] and g[0] != g[2]
    assert np.asarray(group_keys(["A"], "s-s2"))[0] != np.asarray(g)[0]


def test_collision_check(monkeypatch: pytest.MonkeyPatch) -> None:
    from clinical_ml_kits.splitting import groups as mod

    monkeypatch.setattr(mod, "KEY_HEX", 0)  # every key truncated to "" -> collision
    with pytest.raises(ValueError, match="collision"):
        mod.group_keys(["A", "B"], "s-s1")


def test_cv_splitter_is_grouped_and_requires_groups(data) -> None:  # type: ignore[no-untyped-def]
    cv = make_cv_splitter(n_splits=5, seed=7)
    assert isinstance(cv, (GroupKFold, StratifiedGroupKFold))
    g = np.asarray(data.train.groups)
    for tr, va in cv.split(data.train.X, data.train.y, groups=data.train.groups):
        assert not set(g[tr]) & set(g[va])
    with pytest.raises(ValueError, match="groups"):
        next(cv.split(data.train.X, data.train.y))


def test_repeated_rows_of_one_person_never_split() -> None:
    cv = make_cv_splitter(n_splits=3, seed=1)
    Xr = np.arange(60).reshape(30, 2)
    y = np.array([0, 1] * 15)
    groups = group_keys([f"P{i // 3}" for i in range(30)], "r-s1")
    for tr, va in cv.split(Xr, y, groups=groups):
        assert not set(np.asarray(groups)[tr]) & set(np.asarray(groups)[va])


def test_gridsearch_with_groups_uses_train_only(data) -> None:  # type: ignore[no-untyped-def]
    seen: list[int] = []

    class Spy(type(make_cv_splitter(5, 7))):  # type: ignore[misc]
        def split(self, X, y=None, groups=None):  # type: ignore[no-untyped-def]
            seen.append(len(X))
            yield from super().split(X, y, groups)

    spy = Spy(n_splits=5, shuffle=True, random_state=7)
    search = GridSearchCV(
        LogisticRegression(), {"C": [0.1, 1.0]}, cv=spy, scoring="average_precision"
    )
    search.fit(data.train.X, data.train.y, groups=data.train.groups)
    assert seen and all(n == len(data.train.X) for n in seen)


def test_grouped_calibration_folds_respect_groups(data) -> None:  # type: ignore[no-untyped-def]
    folds: list[tuple[set, set]] = []
    base = make_cv_splitter(5, 7)

    class Spy(type(base)):  # type: ignore[misc]
        def split(self, X, y=None, groups=None):  # type: ignore[no-untyped-def]
            g = np.asarray(groups)
            for tr, va in super().split(X, y, groups):
                folds.append((set(g[tr]), set(g[va])))
                yield tr, va

    cal = calibrate_grouped(
        LogisticRegression(),
        data.train.X,
        data.train.y,
        data.train.groups,
        cv=Spy(n_splits=5, shuffle=True, random_state=7),
        method="sigmoid",
    )
    assert folds and all(not (a & b) for a, b in folds)
    p = cal.predict_proba(data.validation.X)[:, 1]
    assert p.shape == (len(data.validation.X),) and ((p >= 0) & (p <= 1)).all()
    with pytest.raises(ValueError, match="groups"):
        calibrate_grouped(
            LogisticRegression(), data.train.X, data.train.y, None, cv=base, method="sigmoid"
        )


def test_isotonic_method(data) -> None:  # type: ignore[no-untyped-def]
    cal = calibrate_grouped(
        LogisticRegression(),
        data.train.X,
        data.train.y,
        data.train.groups,
        cv=make_cv_splitter(5, 7),
        method="isotonic",
    )
    assert cal.predict_proba(data.validation.X).shape[1] == 2
