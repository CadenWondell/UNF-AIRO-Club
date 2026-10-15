"""T061: the shared dataset-adapter contract, run against every registered adapter.

The All of Us adapter joins this suite through a mock query backend once T126–T127 are unblocked
(V-10/V-11); until then it is covered by tests/unit/adapters/test_aou_boundary.py.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from clinical_ml_kits.core.errors import PendingVerification
from clinical_ml_kits.data.registry import available_adapters, get_adapter
from clinical_ml_kits.data.schemas import OBSERVATION_COLUMNS, PERSON_COLUMNS, VISIT_COLUMNS

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = sorted((ROOT / "synthetic" / "golden").glob("*.yaml"))


def _synthetic() -> Any:
    return get_adapter("synthetic_clinical", backend="golden", golden=GOLDEN)


FACTORIES: dict[str, Callable[[], Any]] = {"synthetic_clinical": _synthetic}


def test_every_registered_adapter_is_under_contract() -> None:
    # all_of_us is registered but excluded until its mock-backend realization exists (T127).
    assert set(available_adapters()) - {"all_of_us"} == set(FACTORIES)


@pytest.fixture(params=sorted(FACTORIES))
def adapter(request: pytest.FixtureRequest) -> Any:
    return FACTORIES[request.param]()


def test_metadata(adapter: Any) -> None:
    md = adapter.metadata()
    assert md.id and md.version and md.environment
    assert md.namespace in ("synthetic", "omop")


def test_resolve_own_namespace_only(adapter: Any) -> None:
    md = adapter.metadata()
    real = adapter.resolve("creatinine")
    assert real.namespace == md.namespace and real.logical_id == "creatinine"
    with pytest.raises(PendingVerification):
        adapter.resolve("no_such_logical_concept")


def test_before_is_exclusive(adapter: Any) -> None:
    t = pd.Timestamp("2026-01-01")
    obs = adapter.observations(concepts=["creatinine"], before=t)
    assert len(obs) > 0
    assert (obs.start_time < t).all()
    assert 1.2 not in set(obs.value_num) and 1.5 not in set(obs.value_num)


def test_after_bound(adapter: Any) -> None:
    t = pd.Timestamp("2025-06-01")
    obs = adapter.observations(concepts=["creatinine"], after=t)
    assert (obs.start_time >= t).all()


def test_columns_and_dtypes(adapter: Any) -> None:
    obs = adapter.observations(concepts=["creatinine", "bmi"])
    assert set(OBSERVATION_COLUMNS) <= set(obs.columns)
    assert pd.api.types.is_datetime64_any_dtype(obs.start_time)
    assert set(PERSON_COLUMNS) <= set(adapter.persons().columns)
    assert set(VISIT_COLUMNS) <= set(adapter.visits().columns)


def test_concept_filter(adapter: Any) -> None:
    obs = adapter.observations(concepts=["bmi"])
    assert set(obs.logical_concept) == {"bmi"}
    assert set(obs.domain) == {"measurement"}


def test_person_filter(adapter: Any) -> None:
    pid = adapter.persons().person_id.iloc[0]
    obs = adapter.observations(concepts=["creatinine", "bmi", "sodium"], person_ids=[pid])
    assert set(obs.person_id) <= {pid}


def test_units_canonical(adapter: Any) -> None:
    obs = adapter.observations(concepts=["creatinine", "bmi", "sodium"])
    for concept, rows in obs.groupby("logical_concept"):
        canonical = adapter.resolve(concept).canonical_unit
        assert set(rows.unit) == {canonical}


def test_mapping_version_stamped(adapter: Any) -> None:
    obs = adapter.observations(concepts=["creatinine"])
    assert set(obs.mapping_version) == {adapter.resolve("creatinine").version}
