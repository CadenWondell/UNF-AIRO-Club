"""Golden-patient fixtures: hand-authored synthetic timelines with expected values (R-18).

Golden fixtures serve deterministic unit and edge-case tests only. Kits never run notebooks on
them; ``data_source="synthetic"`` uses a generated population instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

GOLDEN_HEADER = "independently authored synthetic; not derived from any participant data"
OBS_COLUMNS = [
    "person_id",
    "domain",
    "concept_id",
    "value_num",
    "value_concept",
    "unit_raw",
    "start_time",
    "end_time",
    "time_precision",
    "visit_id",
    "source_table",
]
PERSON_COLUMNS = ["person_id", "birth_date", "sex_at_birth", "observation_start", "observation_end"]


@dataclass
class GoldenFixture:
    name: str
    description: str
    persons: pd.DataFrame
    observations: pd.DataFrame
    index: pd.DataFrame
    expected: dict[str, Any] = field(default_factory=dict)
    rules: dict[str, Any] = field(default_factory=dict)


def _check_syn(values: list[Any], what: str) -> None:
    bad = [v for v in values if v is not None and not str(v).startswith("SYN-")]
    if bad:
        raise ValueError(f"golden {what} must be SYN- identifiers: {bad[:3]}")


def load_golden(path: Path) -> GoldenFixture:
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict) or data.get("provenance") != GOLDEN_HEADER:
        raise ValueError(f"{path}: missing provenance header {GOLDEN_HEADER!r}")
    persons = pd.DataFrame(data.get("persons") or [], columns=PERSON_COLUMNS)
    _check_syn(list(persons.person_id), "person ids")
    _check_syn(list(persons.sex_at_birth.dropna()), "sex codes")
    for c in ("birth_date", "observation_start", "observation_end"):
        persons[c] = pd.to_datetime(persons[c])
    obs = pd.DataFrame(data.get("observations") or [])
    for c in OBS_COLUMNS:
        if c not in obs.columns:
            obs[c] = None
    # "label" is a fixture-only column naming rows in expected-value blocks.
    obs = obs[OBS_COLUMNS + (["label"] if "label" in obs.columns else [])].copy()
    _check_syn(list(obs.person_id), "observation person ids")
    _check_syn(list(obs.concept_id), "concept ids")
    obs["start_time"] = pd.to_datetime(obs.start_time.astype(str), format="ISO8601")
    obs["end_time"] = pd.to_datetime(obs.end_time)
    obs["value_num"] = pd.to_numeric(obs.value_num)
    obs["time_precision"] = obs.time_precision.fillna("datetime")
    obs["source_table"] = obs.source_table.fillna("synthetic_golden")
    obs["person_id"] = obs.person_id.astype(object)
    index = pd.DataFrame(
        data.get("index") or [], columns=["person_id", "index_time", "index_visit_id"]
    )
    index["index_time"] = (
        pd.to_datetime(index.index_time.astype(str), format="ISO8601")
        if len(index)
        else (pd.Series(dtype="datetime64[ns]"))
    )
    return GoldenFixture(
        name=str(data.get("fixture", Path(path).stem)),
        description=str(data.get("description", "")),
        persons=persons,
        observations=obs.sort_values(["person_id", "start_time"], kind="stable").reset_index(
            drop=True
        ),
        index=index,
        expected=data.get("expected") or {},
        rules=data.get("rules") or {},
    )
