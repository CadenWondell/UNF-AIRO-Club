"""T065: seeded synthetic population generator."""

from __future__ import annotations

import builtins
import io
import socket
from pathlib import Path

import pandas as pd
import pytest
import yaml
from pydantic import ValidationError

from clinical_ml_kits.adapters.synthetic_clinical.generator import generate
from clinical_ml_kits.adapters.synthetic_clinical.params import PopulationParams, load_params

ROOT = Path(__file__).resolve().parents[3]
PARAMS = ROOT / "tests" / "fixtures" / "synthetic" / "generator_params" / "gen_test.yaml"


def _params(**over: object) -> PopulationParams:
    data = yaml.safe_load(PARAMS.read_text())
    data.update(over)
    return PopulationParams.model_validate(data)


def test_same_seed_identical() -> None:
    a, b = generate(load_params(PARAMS)), generate(load_params(PARAMS))
    pd.testing.assert_frame_equal(a.persons, b.persons)
    pd.testing.assert_frame_equal(a.observations, b.observations)
    c = generate(_params(seed=124))
    assert not c.observations.equals(a.observations)


def test_reads_only_params_and_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[str] = []
    real_open = builtins.open

    def spy(file, *a, **k):  # type: ignore[no-untyped-def]
        opened.append(str(file))
        return real_open(file, *a, **k)

    def no_net(*a, **k):  # type: ignore[no-untyped-def]
        raise AssertionError("network access attempted")

    params = load_params(PARAMS)
    monkeypatch.setattr(builtins, "open", spy)
    monkeypatch.setattr(io, "open", spy)
    monkeypatch.setattr(socket, "socket", no_net)
    generate(params)
    assert opened == []
    monkeypatch.undo()
    opened.clear()
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, *a, **k: (opened.append(str(self)), io.FileIO(str(self)).read().decode())[1],
    )
    load_params(PARAMS)
    assert opened == [str(PARAMS)]


@pytest.mark.parametrize(
    "field,value",
    [
        ("artificial", False),
        ("clinically_realistic", True),
        ("derived_from_participant_data", True),
        ("purpose", "a realistic simulation"),
    ],
)
def test_header_enforced(field: str, value: object) -> None:
    data = yaml.safe_load(PARAMS.read_text())
    data["header"][field] = value
    with pytest.raises(ValidationError, match="header"):
        PopulationParams.model_validate(data)


def test_planted_relationships_must_be_listed() -> None:
    data = yaml.safe_load(PARAMS.read_text())
    data["planted_relationships"] = []
    with pytest.raises(ValidationError, match="planted_relationships"):
        PopulationParams.model_validate(data)


def test_cases_and_controls_produced() -> None:
    pop = generate(load_params(PARAMS))
    assert set(pop.groups.unique()) == {"case", "control"}
    obs = pop.observations
    glucose = obs[obs.logical_concept == "glucose"].merge(
        pop.groups.rename("group").reset_index(), on="person_id"
    )
    assert glucose[glucose.group == "case"].value_num.mean() > 150
    assert glucose[glucose.group == "control"].value_num.mean() < 110
    # some controls lack evidence (probability 0.8) and some cases have workup rows at onset
    ctrl = pop.groups[pop.groups == "control"].index
    with_evidence = set(glucose[glucose.group == "control"].person_id)
    assert 0 < len(with_evidence) < len(ctrl)


def test_controls_change_output() -> None:
    base = generate(load_params(PARAMS))
    assert len(base.persons) == 300
    assert len(generate(_params(n_persons=120)).persons) == 120
    dense = generate(
        _params(
            visit_density={
                **yaml.safe_load(PARAMS.read_text())["visit_density"],
                "visits_per_year": 6.0,
            }
        )
    )
    assert (dense.observations.domain == "visit").sum() > 1.5 * (
        base.observations.domain == "visit"
    ).sum()
    data = yaml.safe_load(PARAMS.read_text())
    data["measurements"]["sodium"]["never_measured"] = 0.9
    sparse = generate(PopulationParams.model_validate(data))
    n_sod = lambda p: p.observations[p.observations.logical_concept == "sodium"].person_id.nunique()  # noqa: E731
    assert n_sod(sparse) < 0.5 * n_sod(base)


def test_case_visit_multiplier_plants_utilization() -> None:
    data = yaml.safe_load(PARAMS.read_text())
    data["visit_density"]["case_rate_multiplier"] = 3.0
    data["planted_relationships"].append(
        {"predictor": "utilization", "effect": "cases visit more often", "note": "artificial"}
    )
    pop = generate(PopulationParams.model_validate(data))
    v = pop.observations[pop.observations.domain == "visit"].groupby("person_id").size()
    g = pop.groups.reindex(v.index)
    assert v[g == "case"].mean() > 2 * v[g == "control"].mean()


def test_times_inside_observation_window() -> None:
    pop = generate(load_params(PARAMS))
    m = pop.observations.merge(pop.persons, on="person_id")
    assert (m.start_time >= m.observation_start).all() and (m.start_time <= m.observation_end).all()


def test_outputs_logical_concepts_and_synthetic_ids() -> None:
    pop = generate(load_params(PARAMS))
    assert pop.observations.person_id.str.startswith("SYN-").all()
    assert pop.persons.sex_at_birth.str.startswith("SYN-").all()
    assert "concept_id" not in pop.observations.columns  # codes are assigned by the adapter


def test_adapter_assigns_syn_codes() -> None:
    from clinical_ml_kits.data.registry import get_adapter

    a = get_adapter("synthetic_clinical", backend="population", params=PARAMS)
    obs = a.observations()
    assert obs.concept_id.str.startswith("SYN-").all()
    assert set(a.persons().person_id) == set(generate(load_params(PARAMS)).persons.person_id)
