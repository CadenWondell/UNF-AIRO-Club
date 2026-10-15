"""T110: kit.to_envelopes produces valid v1.0.0 current_state envelopes."""

from __future__ import annotations

import json

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from clinical_ml_kits.prediction.envelope import DISCLAIMER, PredictionEnvelope
from clinical_ml_kits.preprocessing import make_preprocessor


def test_envelopes(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    m = Pipeline(
        [
            ("preprocess", make_preprocessor(toy_kit.feature_spec)),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    ).fit(toy_data.train.X, toy_data.train.y)
    X = toy_data.validation.X.head(5)
    envs = toy_kit.to_envelopes(m, X)
    assert len(envs) == 5
    groups = set(map(str, toy_data.validation.groups.tolist()))
    for e in envs:
        assert isinstance(e, PredictionEnvelope)
        assert e.contract_version == "1.0.0" and e.kit_id == "toy_binary"
        assert e.prediction_type == "current_state" and e.horizon is None
        assert e.payload.probability_basis == "development_sample"
        assert e.data_environment == "synthetic" and e.subject_ref.startswith("SYN-")
        assert e.calibration_status in ("assessed", "not_assessed", "recalibrated")
        assert e.dataset.id == "synthetic_clinical" and e.disclaimer == DISCLAIMER
        assert set(e.definition_versions.model_dump()) == {
            "phenotype",
            "cohort",
            "kit",
            "feature_registry",
        }
        assert e.model_id and e.model_version == "0.1.0" and e.target.code == "toy_phenotype"
        assert e.as_of.tzinfo is not None
        dumped = e.model_dump_json()
        assert not any(g in dumped for g in groups)
        assert PredictionEnvelope.model_validate(json.loads(dumped)) == e
    assert [e.subject_ref for e in envs] == list(toy_data.validation.person_ids.head(5))
