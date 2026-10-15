"""Shared pytest configuration for the Clinical ML Kit Framework test suite."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
import pytest

matplotlib.use("Agg")

TOY = Path(__file__).resolve().parent / "fixtures" / "kits" / "toy_binary"


@pytest.fixture(scope="session")
def toy_kit() -> Any:
    from clinical_ml_kits import load_kit

    return load_kit(TOY, data_source="synthetic")


@pytest.fixture(scope="session")
def toy_data(toy_kit: Any) -> Any:
    return toy_kit.load()
