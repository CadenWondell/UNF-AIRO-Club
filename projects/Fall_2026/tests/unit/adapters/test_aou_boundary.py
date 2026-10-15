"""T067: the All of Us adapter refuses to run outside the Workbench and holds no queries."""

from __future__ import annotations

import ast
import importlib
import socket
import sys
from pathlib import Path

import pytest

from clinical_ml_kits.core.errors import EnvironmentNotPermitted, PendingVerification

SRC = Path(__file__).resolve().parents[3] / "src" / "clinical_ml_kits" / "adapters" / "all_of_us"


def test_import_has_no_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_net(*a, **k):  # type: ignore[no-untyped-def]
        raise AssertionError("network at import time")

    monkeypatch.setattr(socket, "socket", no_net)
    sys.modules.pop("clinical_ml_kits.adapters.all_of_us.adapter", None)
    importlib.import_module("clinical_ml_kits.adapters.all_of_us.adapter")


def test_refused_outside_workbench() -> None:
    from clinical_ml_kits.data.registry import get_adapter

    with pytest.raises(EnvironmentNotPermitted, match="Researcher Workbench"):
        get_adapter("all_of_us")


def test_refused_even_with_legacy_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    # V-10 is unverified: guessed markers must not unlock the adapter.
    for var in ("WORKSPACE_CDR", "GOOGLE_PROJECT", "WORKSPACE_BUCKET", "GOOGLE_CLOUD_PROJECT"):
        monkeypatch.setenv(var, "x")
    from clinical_ml_kits.data.registry import get_adapter

    with pytest.raises(EnvironmentNotPermitted):
        get_adapter("all_of_us")


@pytest.fixture()
def mocked_workbench(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    from clinical_ml_kits.adapters.all_of_us import adapter as mod

    monkeypatch.setattr(mod, "is_all_of_us_workbench", lambda _defs: True)
    return mod.AllOfUsAdapter.create()


def test_policy_and_namespace(mocked_workbench) -> None:  # type: ignore[no-untyped-def]
    assert mocked_workbench.policy().name == "all_of_us_workbench"
    md = mocked_workbench.metadata()
    assert md.namespace == "omop" and md.environment == "all_of_us_workbench"


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.persons(),
        lambda a: a.observations(concepts=["creatinine"]),
        lambda a: a.visits(),
        lambda a: a.index_candidates(["visit_outpatient"]),
    ],
)
def test_data_methods_pending(mocked_workbench, call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(PendingVerification) as exc:
        call(mocked_workbench)
    assert exc.value.item_id == "V-10/V-11"


def test_resolve_requires_verified_omop(mocked_workbench) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(PendingVerification):
        mocked_workbench.resolve("creatinine")


def test_no_sql_or_clients_in_source() -> None:
    import re

    for f in SRC.glob("*.py"):
        text = f.read_text()
        assert not re.search(r"\bSELECT\b|\bFROM\s+`|bigquery|google\.cloud", text, re.I), f
        ast.parse(text)
