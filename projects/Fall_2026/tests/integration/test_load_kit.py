"""T095: load_kit / Kit.load on the toy kit (synthetic population, hidden test partition)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pytest

from clinical_ml_kits import load_kit
from clinical_ml_kits.core.errors import EnvironmentNotPermitted, KitValidationError
from clinical_ml_kits.splitting.groups import OpaqueGroups

FIX = Path(__file__).resolve().parents[1] / "fixtures"
TOY = FIX / "kits" / "toy_binary"


@pytest.fixture(scope="module")
def kit():  # type: ignore[no-untyped-def]
    return load_kit(TOY, data_source="synthetic")


@pytest.fixture(scope="module")
def data(kit):  # type: ignore[no-untyped-def]
    return kit.load()


def test_validates_at_synthetic_level(kit) -> None:  # type: ignore[no-untyped-def]
    assert kit.kit_id == "toy_binary" and kit.environment == "synthetic"
    assert kit.validation.level == "synthetic"


def test_all_of_us_refused_before_data_access() -> None:
    with pytest.raises(EnvironmentNotPermitted):
        load_kit(TOY, data_source="all_of_us")


def test_all_of_us_also_refused_for_provisional_values(monkeypatch: pytest.MonkeyPatch) -> None:
    from clinical_ml_kits.adapters.all_of_us import adapter as aou

    monkeypatch.setattr(aou, "is_all_of_us_workbench", lambda _d: True)
    with pytest.raises(KitValidationError, match="workbench"):
        load_kit(TOY, data_source="all_of_us")


def test_unknown_data_source() -> None:
    with pytest.raises(ValueError):
        load_kit(TOY, data_source="laptop_with_real_data")


def test_population_not_golden(kit, data) -> None:  # type: ignore[no-untyped-def]
    m = data.run_manifest
    assert m.synthetic_population["path"].endswith("toy_binary.yaml")
    assert m.synthetic_population["seed"] == 20261015
    assert m.synthetic_population["n_persons"] == 1500
    assert "golden" not in kit.adapter.source_label


def test_partitions_and_hidden_test(data) -> None:  # type: ignore[no-untyped-def]
    assert not hasattr(data, "test")
    for p in ("train", "validation", "test"):
        assert data.split_manifest.partitions[p].n_pos >= 10
    for ds in (data.train, data.validation):
        assert isinstance(ds.groups, OpaqueGroups) and len(ds.groups) == len(ds.X)
        assert not any("group" in c or "person" in c for c in ds.X.columns)
        assert set(ds.y.unique()) == {0, 1}


def test_one_row_per_person(data) -> None:  # type: ignore[no-untyped-def]
    ids = pd.concat([data.train.person_ids, data.validation.person_ids])
    assert ids.is_unique


def test_two_rows_for_one_person_rejected(kit, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    from clinical_ml_kits.core import kit as kitmod

    real = kitmod.build_cohort

    def doubled(*a, **k):  # type: ignore[no-untyped-def]
        r = real(*a, **k)
        r.table = pd.concat([r.table, r.table.iloc[[0]]], ignore_index=True)
        return r

    monkeypatch.setattr(kitmod, "build_cohort", doubled)
    with pytest.raises(KitValidationError, match="one row per person"):
        kit.load()


def test_min_features_present_applied_before_split(kit, caplog: pytest.LogCaptureFixture) -> None:  # type: ignore[no-untyped-def]
    with caplog.at_level(logging.INFO, logger="clinical_ml_kits"):
        d = kit.load()
    assert any("min_features_present" in r.getMessage() for r in caplog.records)
    assert d.run_manifest.split_manifest_digest == d.split_manifest.digest
    present = d.train.X.notna().sum(axis=1)
    assert (present >= 2).all()


def test_feature_columns_and_label_concepts_excluded(data) -> None:  # type: ignore[no-untyped-def]
    cols = list(data.train.X.columns)
    assert "fx_bmi__latest" in cols and "fx_outpatient_visits__count" in cols
    assert not any(c.startswith(("fx_dx", "fx_marker")) for c in cols)


def test_run_manifest_populated(data) -> None:  # type: ignore[no-untyped-def]
    m = data.run_manifest
    assert m.control_sampling_seed == 11 and m.split_salt_version == 1
    assert m.split_salt == "toy_binary-s1" and m.kit_id == "toy_binary"
    assert m.concept_set_versions["fx_bmi"] == "0.1.0"
    assert m.dataset_id == "synthetic_clinical" and m.environment == "synthetic"
    assert m.kit_definition_hash


def test_describe_lists_exclusions_and_provisional(kit) -> None:  # type: ignore[no-untyped-def]
    text = kit.describe()
    assert "fx_dx" in text and "fx_marker" in text
    assert "PROVISIONAL" in text and "temporal_policy.same_day" in text
    assert "current_state" in text


def test_summary(data) -> None:  # type: ignore[no-untyped-def]
    s = data.summary()
    assert list(s.index) == ["train", "validation", "test"]
    assert {"n", "n_pos", "prevalence"} <= set(s.columns)
