"""T102: reliability bins, Brier score, calibration intercept and slope."""

from __future__ import annotations

import numpy as np
import pytest

from clinical_ml_kits.evaluation.calibration import calibration_summary, reliability_bins

RNG = np.random.default_rng(0)
P = RNG.uniform(0.05, 0.95, 20000)
Y = (RNG.random(20000) < P).astype(int)


@pytest.mark.parametrize("strategy", ["quantile", "uniform"])
def test_bins(strategy: str) -> None:
    b = reliability_bins(Y, P, bins=10, strategy=strategy)
    assert len(b) == 10 and b.n.sum() == len(Y)
    assert {"bin", "n", "mean_predicted", "observed_rate"} <= set(b.columns)
    if strategy == "quantile":
        assert b.n.max() - b.n.min() <= 2
    assert np.allclose(b.mean_predicted, b.observed_rate, atol=0.05)


def test_perfectly_calibrated_intercept_slope() -> None:
    s = calibration_summary(Y, P)
    assert s.slope == pytest.approx(1.0, abs=0.08)
    assert s.intercept == pytest.approx(0.0, abs=0.05)
    assert s.brier == pytest.approx(np.mean((P - Y) ** 2))


def test_miscalibration_detected() -> None:
    s = calibration_summary(Y, np.clip(P * 0.5, 0.01, 0.99))
    assert s.intercept > 0.3


def test_text_never_claims_clinical_risk() -> None:
    text = calibration_summary(Y, P).describe().lower()
    assert "development sample" in text
    assert "not a clinical risk score" in text or "not clinical risk" in text
