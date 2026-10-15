"""Synthetic population parameter files (``synthetic/generator_params/<kit_id>.yaml``)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict

PURPOSE = "framework testing and student workflow only; not a prevalence or effect-size simulation"


class ParamsHeader(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artificial: Literal[True]
    clinically_realistic: Literal[False]
    derived_from_participant_data: Literal[False]
    purpose: Literal[
        "framework testing and student workflow only; not a prevalence or effect-size simulation"
    ]


class PopulationParams(BaseModel):
    model_config = ConfigDict(extra="allow")
    header: ParamsHeader


def load_params(path: Path) -> PopulationParams:
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path}: params must be a mapping")
    return PopulationParams.model_validate(data)
