"""T093: each leakage class raises its named LeakageError subclass (SC-005)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from clinical_ml_kits.core.errors import (
    LabelLeakageError,
    PatientLeakageError,
    PreprocessingLeakageError,
    ProhibitedFeatureError,
    SameDayLeakageError,
    TargetLeakageError,
    TemporalLeakageError,
)
from clinical_ml_kits.leakage import checks
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy

COHORT = pd.DataFrame(
    {
        "person_id": ["P1", "P2"],
        "index_time": pd.to_datetime(["2026-01-01", "2026-01-01"]),
        "index_visit_id": ["V-IDX-1", None],
    }
)


def pol(same_day: str = "include", enc: bool = False) -> ResolvedTemporalPolicy:
    return ResolvedTemporalPolicy.from_values(
        same_day=same_day, washout="P0D", lookback="P365D", exclude_index_encounter=enc
    )


def lineage(time: str, visit: str = "V-X", pid: str = "P1") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "person_id": [pid],
            "feature": ["sodium"],
            "max_source_time": [pd.Timestamp(time)],
            "visit_id": [visit],
        }
    )


def test_patient_leakage() -> None:
    checks.check_patients({"train": {"A", "B"}, "validation": {"C"}, "test": {"D"}})
    with pytest.raises(PatientLeakageError, match="B"):
        checks.check_patients({"train": {"A", "B"}, "validation": {"B"}, "test": {"D"}})


def test_temporal_leakage_post_index_row() -> None:
    checks.check_lineage(lineage("2025-12-31"), COHORT, pol())
    with pytest.raises(TemporalLeakageError):
        checks.check_lineage(lineage("2026-01-02"), COHORT, pol())


def test_same_day_leakage() -> None:
    checks.check_lineage(lineage("2026-01-01"), COHORT, pol("include"))
    with pytest.raises(SameDayLeakageError):
        checks.check_lineage(lineage("2026-01-01T08:00"), COHORT, pol("exclude_index_day"))
    with pytest.raises(SameDayLeakageError):
        checks.check_lineage(lineage("2025-12-31", visit="V-IDX-1"), COHORT, pol(enc=True))


def test_target_concept_overlap() -> None:
    checks.check_target_overlap({"bmi": "bmi"}, {"t2d_diagnosis"}, set())
    with pytest.raises(TargetLeakageError, match="hba1c"):
        checks.check_target_overlap({"hba1c": "hba1c"}, {"hba1c"}, set())


def test_justified_inclusion_passes() -> None:
    checks.check_target_overlap({"hba1c": "hba1c"}, {"hba1c"}, {"hba1c"})
    checks.check_prohibited({"hba1c": ("hba1c", "measurement")}, [{"feature": "hba1c"}], {"hba1c"})


def test_label_leakage_undeclared_label_source() -> None:
    # glucose drives the case rule but is not declared label-defining: still caught
    with pytest.raises(LabelLeakageError, match="glucose"):
        checks.check_label_sources({"glucose": "glucose"}, label_source_concepts={"glucose"})


def test_prohibited_feature() -> None:
    with pytest.raises(ProhibitedFeatureError):
        checks.check_prohibited({"bmi": ("bmi", "measurement")}, [{"feature": "bmi"}], set())
    with pytest.raises(ProhibitedFeatureError):
        checks.check_prohibited({"x": ("dialysis", "procedure")}, [{"domain": "procedure"}], set())
    with pytest.raises(ProhibitedFeatureError):
        checks.check_prohibited({"x": ("egfr", "measurement")}, [{"concept": "egfr"}], set())


def test_preprocessing_boundary() -> None:
    rng = np.random.default_rng(0)
    X_train, y_train = rng.normal(size=(80, 2)), np.array([0, 1] * 40)
    X_all = np.vstack([X_train, rng.normal(size=(20, 2))])
    good = Pipeline(
        [("imp", SimpleImputer()), ("sc", StandardScaler()), ("m", LogisticRegression())]
    ).fit(X_train, y_train)
    checks.check_preprocessing_fit(good, n_train=80)
    leaky = Pipeline([("sc", StandardScaler().fit(X_all)), ("m", LogisticRegression())])
    leaky.named_steps["m"].fit(leaky.named_steps["sc"].transform(X_train), y_train)
    with pytest.raises(PreprocessingLeakageError):
        checks.check_preprocessing_fit(leaky, n_train=80)
