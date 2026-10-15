"""Column contracts for adapter outputs (data-model § 1)."""

from __future__ import annotations

import pandas as pd

PERSON_COLUMNS = ["person_id", "birth_date", "sex_at_birth", "observation_start", "observation_end"]
OBSERVATION_COLUMNS = [
    "person_id",
    "domain",
    "concept_id",
    "logical_concept",
    "feature_key",
    "value_num",
    "value_concept",
    "unit_raw",
    "unit",
    "start_time",
    "end_time",
    "time_precision",
    "visit_id",
    "source_table",
    "mapping_version",
]
VISIT_COLUMNS = ["person_id", "visit_id", "visit_type", "start_time", "end_time", "time_precision"]
DOMAINS = (
    "measurement",
    "condition",
    "drug",
    "procedure",
    "visit",
    "observation",
    "survey",
    "device",
)


def empty_observations() -> pd.DataFrame:
    df = pd.DataFrame({c: pd.Series(dtype=object) for c in OBSERVATION_COLUMNS})
    df["start_time"] = pd.Series(dtype="datetime64[ns]")
    df["end_time"] = pd.Series(dtype="datetime64[ns]")
    df["value_num"] = pd.Series(dtype=float)
    return df


def check_columns(df: pd.DataFrame, required: list[str], what: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{what} is missing columns {missing}")
