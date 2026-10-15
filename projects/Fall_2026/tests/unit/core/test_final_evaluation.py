"""T108: kit.final_evaluation — guarded, logged once, isolation-checked, threshold reused."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from clinical_ml_kits import load_kit
from clinical_ml_kits.core.errors import PreprocessingLeakageError
from clinical_ml_kits.evaluation import evaluate_binary
from clinical_ml_kits.preprocessing import make_preprocessor

TOY = Path(__file__).resolve().parents[2] / "fixtures" / "kits" / "toy_binary"


@pytest.fixture()
def fresh():  # type: ignore[no-untyped-def]
    k = load_kit(TOY)
    return k, k.load()


def _pipe(kit, est):  # type: ignore[no-untyped-def]
    return Pipeline([("preprocess", make_preprocessor(kit.feature_spec)), ("model", est)])


def test_logged_once_and_warns_on_repeat(fresh, caplog: pytest.LogCaptureFixture) -> None:  # type: ignore[no-untyped-def]
    kit, data = fresh
    m = _pipe(kit, LogisticRegression(max_iter=1000)).fit(data.train.X, data.train.y)
    with caplog.at_level(logging.INFO, logger="clinical_ml_kits"):
        report = kit.final_evaluation(m)
    assert (
        len([r for r in caplog.records if getattr(r, "ckit_event", "") == "final_test_access"]) == 1
    )
    assert report.test.n == data.split_manifest.partitions["test"].n
    assert len(data.run_manifest.test_access_log) == 1
    with pytest.warns(UserWarning, match="again"):
        kit.final_evaluation(m)


def test_threshold_from_validation_reused(fresh) -> None:  # type: ignore[no-untyped-def]
    kit, data = fresh
    m = _pipe(kit, LogisticRegression(max_iter=1000)).fit(data.train.X, data.train.y)
    val = evaluate_binary(
        data.validation.y, m.predict_proba(data.validation.X)[:, 1], kit.definition.threshold_rule
    )
    report = kit.final_evaluation(m)
    assert report.threshold == pytest.approx(val.threshold)
    assert report.test.threshold == report.threshold and report.test.threshold_rule == "reused"
    assert "auroc" in report.test_ci


@pytest.mark.parametrize(
    "est",
    [
        LogisticRegression(max_iter=1000),
        RandomForestClassifier(n_estimators=30, random_state=0),
        GradientBoostingClassifier(random_state=0),
        SVC(probability=True, random_state=0),
        KNeighborsClassifier(n_neighbors=15),
    ],
    ids=lambda e: type(e).__name__,
)
def test_accepts_standard_estimators(fresh, est) -> None:  # type: ignore[no-untyped-def]
    kit, data = fresh
    m = _pipe(kit, est).fit(data.train.X, data.train.y)
    assert 0 <= kit.final_evaluation(m).test.metrics["auroc"] <= 1


def test_preprocessing_isolation_enforced(fresh) -> None:  # type: ignore[no-untyped-def]
    import pandas as pd

    kit, data = fresh
    leaky = _pipe(kit, LogisticRegression(max_iter=1000))
    both = pd.concat([data.train.X, data.validation.X])
    leaky.named_steps["preprocess"].fit(both)
    Z = leaky.named_steps["preprocess"].transform(data.train.X)
    leaky.named_steps["model"].fit(Z, data.train.y)
    with pytest.raises(PreprocessingLeakageError):
        kit.final_evaluation(leaky)


def test_non_pipeline_warns(fresh) -> None:  # type: ignore[no-untyped-def]
    kit, data = fresh
    X = data.train.X.fillna(0)
    m = LogisticRegression(max_iter=1000).fit(StandardScaler().fit_transform(X), data.train.y)

    class Wrapped:
        def predict_proba(self, X):  # type: ignore[no-untyped-def]
            return m.predict_proba(X.fillna(0).to_numpy())

    with pytest.warns(UserWarning, match="Pipeline"):
        kit.final_evaluation(Wrapped())
