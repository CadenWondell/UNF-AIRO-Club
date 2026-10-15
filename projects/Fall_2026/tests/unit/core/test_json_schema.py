"""T033: committed JSON Schemas equal freshly generated ones (byte for byte)."""

from __future__ import annotations

from pathlib import Path

import pytest

from clinical_ml_kits.core.schema_export import SCHEMAS, render_schema

DOCS = Path(__file__).resolve().parents[3] / "docs" / "schemas"


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_committed_schema_is_current(name: str) -> None:
    committed = (DOCS / f"{name}.schema.json").read_text()
    assert committed == render_schema(name), f"regenerate with `ckit schemas` ({name})"


def test_expected_schema_set() -> None:
    assert set(SCHEMAS) == {"kit-definition", "prediction-envelope", "provenance"}


def test_unverified_sentinel_documented() -> None:
    assert '"UNVERIFIED"' in render_schema("kit-definition")
