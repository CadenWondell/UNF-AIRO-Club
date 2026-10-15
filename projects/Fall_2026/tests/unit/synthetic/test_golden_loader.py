"""T055: golden-patient YAML format and loader."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from clinical_ml_kits.adapters.synthetic_clinical.golden import GOLDEN_HEADER, load_golden

GOOD = f"""provenance: "{GOLDEN_HEADER}"
fixture: tiny
description: "tiny"
persons:
  - {{person_id: SYN-G-1, birth_date: 1970-01-01, sex_at_birth: SYN-SEX-F,
     observation_start: 2020-01-01, observation_end: 2026-12-31}}
observations:
  - {{person_id: SYN-G-1, domain: measurement, concept_id: SYN-CREATININE, value_num: 0.9,
     unit_raw: mg/dL, start_time: 2025-01-01, time_precision: date, visit_id: V1}}
  - {{person_id: SYN-G-1, domain: visit, concept_id: SYN-VISIT-OUTPATIENT,
     start_time: "2025-01-01T09:30:00", time_precision: datetime, visit_id: V1}}
index:
  - {{person_id: SYN-G-1, index_time: 2026-01-01, index_visit_id: null}}
expected:
  latest: 0.9
"""


def test_loads(tmp_path: Path) -> None:
    p = tmp_path / "g.yaml"
    p.write_text(GOOD)
    g = load_golden(p)
    assert list(g.persons.person_id) == ["SYN-G-1"]
    obs = g.observations
    assert {
        "person_id",
        "domain",
        "concept_id",
        "value_num",
        "unit_raw",
        "start_time",
        "time_precision",
        "visit_id",
        "source_table",
    } <= set(obs.columns)
    assert pd.api.types.is_datetime64_any_dtype(obs.start_time)
    assert g.expected == {"latest": 0.9}
    assert g.index.index_time.iloc[0] == pd.Timestamp("2026-01-01")


def test_header_required(tmp_path: Path) -> None:
    p = tmp_path / "g.yaml"
    p.write_text(GOOD.replace(GOLDEN_HEADER, "copied from somewhere"))
    with pytest.raises(ValueError, match="provenance"):
        load_golden(p)


def test_non_synthetic_ids_rejected(tmp_path: Path) -> None:
    p = tmp_path / "g.yaml"
    p.write_text(GOOD.replace("SYN-CREATININE", "3016723"))
    with pytest.raises(ValueError, match="SYN-"):
        load_golden(p)
