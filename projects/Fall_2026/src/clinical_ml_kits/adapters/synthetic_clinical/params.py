"""Synthetic population parameter files (``synthetic/generator_params/<kit_id>.yaml``).

Every params file declares, in its header, that the population is artificial, not clinically
realistic, not derived from participant data, and not a prevalence or effect-size simulation.
Every deliberately planted case/control difference in a non-label-defining predictor must be
listed under ``planted_relationships``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

PURPOSE = "framework testing and student workflow only; not a prevalence or effect-size simulation"
_STRICT = ConfigDict(extra="forbid")


class ParamsHeader(BaseModel):
    model_config = _STRICT
    artificial: Literal[True]
    clinically_realistic: Literal[False]
    derived_from_participant_data: Literal[False]
    purpose: Literal[
        "framework testing and student workflow only; not a prevalence or effect-size simulation"
    ]


class Range(BaseModel):
    model_config = _STRICT
    min: float
    max: float

    @model_validator(mode="after")
    def _ordered(self) -> Range:
        if self.max < self.min:
            raise ValueError("max < min")
        return self


class Normal(BaseModel):
    model_config = _STRICT
    mean: float
    sd: float = Field(ge=0)


class Calendar(BaseModel):
    model_config = _STRICT
    start: date
    end: date


class PersonSpec(BaseModel):
    model_config = _STRICT
    age_at_start: Range
    sex_codes: dict[str, float]
    observation_years: Range

    @model_validator(mode="after")
    def _codes(self) -> PersonSpec:
        if any(not k.startswith("SYN-") for k in self.sex_codes):
            raise ValueError("sex codes must be SYN- codes")
        if abs(sum(self.sex_codes.values()) - 1) > 1e-9:
            raise ValueError("sex code probabilities must sum to 1")
        return self


class AnchorSpec(BaseModel):
    model_config = _STRICT
    min_history_days: int = Field(ge=0)
    min_tail_days: int = Field(ge=0)


class VisitDensity(BaseModel):
    model_config = _STRICT
    visits_per_year: float = Field(gt=0)
    case_rate_multiplier: float = Field(default=1.0, gt=0)
    visit_type_mix: dict[str, float]
    anchor_visit_type: str = "visit_outpatient"

    @model_validator(mode="after")
    def _mix(self) -> VisitDensity:
        if abs(sum(self.visit_type_mix.values()) - 1) > 1e-9:
            raise ValueError("visit_type_mix must sum to 1")
        return self


class MeasurementSpec(BaseModel):
    model_config = _STRICT
    unit: str
    p_per_visit: float = Field(ge=0, le=1)
    never_measured: float = Field(default=0.0, ge=0, le=1)
    decimals: int = Field(default=1, ge=0)
    clip: tuple[float, float] | None = None
    control: Normal
    case: Normal | None = None


class EventSpec(BaseModel):
    model_config = _STRICT
    concept: str
    domain: Literal["measurement", "condition", "drug", "procedure", "observation"]
    group: Literal["case", "control", "all"] = "all"
    probability: float = Field(default=1.0, ge=0, le=1)
    offsets_days: list[int] = Field(min_length=1)
    value: Normal | None = None
    unit: str | None = None
    decimals: int = Field(default=1, ge=0)
    visit_type: str = "visit_outpatient"
    note: str = ""

    @model_validator(mode="after")
    def _measurement_value(self) -> EventSpec:
        if self.domain == "measurement" and (self.value is None or self.unit is None):
            raise ValueError("measurement events need value and unit")
        return self


class Workup(BaseModel):
    model_config = _STRICT
    concepts: list[str] = Field(default_factory=list)
    probability: float = Field(default=1.0, ge=0, le=1)


class Events(BaseModel):
    model_config = _STRICT
    case_recipe: list[EventSpec] = Field(min_length=1)
    control_recipe: list[EventSpec] = Field(min_length=1)
    background: list[EventSpec] = Field(default_factory=list)
    exclusions: list[EventSpec] = Field(default_factory=list)
    workup_at_onset: Workup = Field(default_factory=Workup)


class ConditionSpec(BaseModel):
    model_config = _STRICT
    domain: Literal["condition", "drug", "procedure", "observation"] = "condition"
    case_rate: float = Field(ge=0, le=1)
    control_rate: float = Field(ge=0, le=1)
    timing: Literal["before_anchor", "any"] = "any"


class PlantedRelationship(BaseModel):
    model_config = _STRICT
    predictor: str
    effect: str = Field(min_length=1)
    note: str = Field(min_length=1)


class PopulationParams(BaseModel):
    model_config = _STRICT
    header: ParamsHeader
    generator_version: Literal[1]
    seed: int
    n_persons: int = Field(gt=0)
    calendar: Calendar
    person: PersonSpec
    case_fraction: float = Field(gt=0, lt=1)
    anchor: AnchorSpec
    visit_density: VisitDensity
    measurements: dict[str, MeasurementSpec] = Field(default_factory=dict)
    conditions: dict[str, ConditionSpec] = Field(default_factory=dict)
    events: Events
    planted_relationships: list[PlantedRelationship] = Field(default_factory=list)
    notes: str = ""

    @model_validator(mode="after")
    def _planted_listed(self) -> PopulationParams:
        listed = {p.predictor for p in self.planted_relationships}
        need: set[str] = set()
        for k, m in self.measurements.items():
            if m.case is not None and m.case != m.control:
                need.add(k)
        for k, c in self.conditions.items():
            if c.case_rate != c.control_rate:
                need.add(k)
        if self.visit_density.case_rate_multiplier != 1.0:
            need.add("utilization")
        for e in self.events.background:
            if e.group != "all":
                need.add(e.concept)
        if self.events.workup_at_onset.concepts:
            need.add("index_day_workup")
        missing = sorted(need - listed)
        if missing:
            raise ValueError(f"planted_relationships must list every planted signal: {missing}")
        if self.calendar.end <= self.calendar.start:
            raise ValueError("calendar.end must follow calendar.start")
        return self


def load_params(path: Path) -> PopulationParams:
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path}: params must be a mapping")
    return PopulationParams.model_validate(data)
