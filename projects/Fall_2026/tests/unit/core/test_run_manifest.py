"""T020: seeds and RunManifest (research R-19)."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression

from clinical_ml_kits.core.run_manifest import RunManifest
from clinical_ml_kits.core.seeds import numpy_rng, sklearn_random_state

R19_FIELDS = {
    "framework_version",
    "git_commit",
    "kit_id",
    "kit_definition_hash",
    "kit_version",
    "phenotype_version",
    "concept_set_versions",
    "feature_registry_version",
    "dataset_id",
    "dataset_version",
    "adapter",
    "environment",
    "seed",
    "split_salt",
    "split_salt_version",
    "split_manifest_digest",
    "control_sampling_seed",
    "synthetic_population",
    "library_versions",
    "test_access_log",
}


def _manifest(**over: object) -> RunManifest:
    base: dict[str, object] = dict(
        kit_id="toy_binary",
        kit_definition_hash="abc",
        kit_version="0.1.0",
        phenotype_version="0.1.0",
        concept_set_versions={"creatinine": "0.1.0"},
        feature_registry_version="0.1.0",
        dataset_id="synthetic_clinical",
        dataset_version="0.1.0",
        adapter="synthetic_clinical",
        environment="synthetic",
        seed=7,
        split_salt="toy-s1",
        split_salt_version=1,
        split_manifest_digest="d1",
        control_sampling_seed=11,
        synthetic_population={"path": "synthetic/generator_params/toy_binary.yaml", "seed": 3},
    )
    base.update(over)
    return RunManifest(**base)  # type: ignore[arg-type]


def test_seed_drives_numpy_and_sklearn_deterministically() -> None:
    a = numpy_rng(42).normal(size=5)
    b = numpy_rng(42).normal(size=5)
    assert np.array_equal(a, b)
    assert sklearn_random_state(42) == sklearn_random_state(42)
    X = numpy_rng(1).normal(size=(50, 3))
    y = (X[:, 0] > 0).astype(int)
    m1 = LogisticRegression(random_state=sklearn_random_state(5)).fit(X, y)
    m2 = LogisticRegression(random_state=sklearn_random_state(5)).fit(X, y)
    assert np.array_equal(m1.coef_, m2.coef_)


def test_manifest_has_all_r19_fields() -> None:
    assert R19_FIELDS <= set(RunManifest.model_fields)
    m = _manifest()
    assert m.framework_version
    assert {"numpy", "pandas", "scikit-learn", "pydantic"} <= set(m.library_versions)


def test_content_hash_stable_and_sensitive() -> None:
    m1, m2 = _manifest(), _manifest()
    assert m1.content_hash() == m2.content_hash()
    for field, value in [
        ("seed", 8),
        ("split_salt", "x"),
        ("kit_definition_hash", "zzz"),
        ("concept_set_versions", {"creatinine": "0.2.0"}),
    ]:
        assert _manifest(**{field: value}).content_hash() != m1.content_hash(), field


def test_test_access_is_recorded() -> None:
    m = _manifest()
    m.record_test_access()
    assert len(m.test_access_log) == 1
