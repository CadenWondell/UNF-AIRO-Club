"""Seeded synthetic population generator (R-18).

Produces an artificial, OMOP-shaped person + long-format observation population from one
``PopulationParams`` object. It performs no file or network I/O, is never fitted to or sampled
from participant data, and makes no attempt to reproduce real distributions. Output rows carry
logical concept ids; the synthetic adapter assigns the fictional ``SYN-`` codes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from clinical_ml_kits.adapters.synthetic_clinical.params import EventSpec, PopulationParams

DAY = np.timedelta64(1, "D")


@dataclass
class Population:
    persons: pd.DataFrame
    observations: pd.DataFrame
    groups: pd.Series  # person_id -> "case" | "control" (generator recipe group, not a label)
    seed: int


def _days(a: NDArray[Any]) -> NDArray[Any]:
    return np.round(a).astype("int64") * DAY


def generate(params: PopulationParams) -> Population:
    p = params
    rng = np.random.default_rng(p.seed)
    n = p.n_persons
    pids = np.array([f"SYN-P-{i:06d}" for i in range(1, n + 1)], dtype=object)

    # ---------------------------------------------------------------- persons
    cal_start = np.datetime64(p.calendar.start, "D")
    cal_end = np.datetime64(p.calendar.end, "D")
    span_days = (cal_end - cal_start) / DAY
    years = rng.uniform(p.person.observation_years.min, p.person.observation_years.max, n)
    obs_days = np.minimum(years * 365.25, span_days)
    start_off = rng.uniform(0, 1, n) * (span_days - obs_days)
    obs_start = cal_start + _days(start_off)
    obs_end = obs_start + _days(obs_days)
    age = rng.uniform(p.person.age_at_start.min, p.person.age_at_start.max, n)
    birth = obs_start - _days(age * 365.25)
    sex_codes = sorted(p.person.sex_codes)
    sex = rng.choice(sex_codes, size=n, p=[p.person.sex_codes[c] for c in sex_codes])
    is_case = rng.random(n) < p.case_fraction
    groups = pd.Series(
        np.where(is_case, "case", "control"), index=pd.Index(pids, name="person_id"), name="group"
    )
    persons = pd.DataFrame(
        {
            "person_id": pids,
            "birth_date": pd.to_datetime(birth),
            "sex_at_birth": sex,
            "observation_start": pd.to_datetime(obs_start),
            "observation_end": pd.to_datetime(obs_end),
        }
    )

    # ---------------------------------------------------------------- anchors
    lo = obs_start + p.anchor.min_history_days * DAY
    hi = obs_end - p.anchor.min_tail_days * DAY
    width = np.maximum((hi - lo) / DAY, 0)
    anchor = lo + _days(rng.uniform(0, 1, n) * width)
    anchor = np.where(hi < lo, obs_start + _days(obs_days / 2), anchor)

    # ---------------------------------------------------------------- visits
    vd = p.visit_density
    rate = vd.visits_per_year * np.where(is_case, vd.case_rate_multiplier, 1.0)
    counts = rng.poisson(rate * obs_days / 365.25)
    v_person = np.repeat(np.arange(n), counts)
    v_date = obs_start[v_person] + _days(rng.uniform(0, 1, len(v_person)) * obs_days[v_person])
    types = sorted(vd.visit_type_mix)
    v_type = rng.choice(types, size=len(v_person), p=[vd.visit_type_mix[t] for t in types])
    # every person has an outpatient visit at their anchor date
    v_person = np.concatenate([v_person, np.arange(n)])
    v_date = np.concatenate([v_date, anchor])
    v_type = np.concatenate([v_type, np.full(n, vd.anchor_visit_type)])
    v_anchor = np.concatenate([np.zeros(len(v_date) - n, bool), np.ones(n, bool)])
    visits = (
        pd.DataFrame(
            {
                "pi": v_person,
                "date": v_date.astype("datetime64[ns]"),
                "type": v_type,
                "is_anchor": v_anchor,
            }
        )
        .sort_values(["pi", "date", "is_anchor"], kind="stable")
        .reset_index(drop=True)
    )
    visits["k"] = visits.groupby("pi").cumcount() + 1
    visits["visit_id"] = [
        f"SYN-V-{pi + 1:06d}-{k:04d}" for pi, k in zip(visits.pi, visits.k, strict=True)
    ]
    anchor_visit = visits[visits.is_anchor].set_index("pi").visit_id

    rows: list[pd.DataFrame] = [
        pd.DataFrame(
            {
                "pi": visits.pi,
                "domain": "visit",
                "logical_concept": visits.type,
                "value_num": np.nan,
                "unit_raw": None,
                "start_time": visits.date,
                "visit_id": visits.visit_id,
            }
        )
    ]

    # ---------------------------------------------------------------- measurements at visits
    for concept in sorted(p.measurements):
        spec = p.measurements[concept]
        never = rng.random(n) < spec.never_measured
        take = (rng.random(len(visits)) < spec.p_per_visit) & ~never[visits.pi.to_numpy()]
        sel = visits[take]
        case_rows = is_case[sel.pi.to_numpy()]
        dist_case = spec.case or spec.control
        mean = np.where(case_rows, dist_case.mean, spec.control.mean)
        sd = np.where(case_rows, dist_case.sd, spec.control.sd)
        values = rng.normal(mean, sd)
        if spec.clip:
            values = np.clip(values, *spec.clip)
        rows.append(
            pd.DataFrame(
                {
                    "pi": sel.pi,
                    "domain": "measurement",
                    "logical_concept": concept,
                    "value_num": np.round(values, spec.decimals),
                    "unit_raw": spec.unit,
                    "start_time": sel.date,
                    "visit_id": sel.visit_id,
                }
            )
        )

    # ---------------------------------------------------------------- workup at onset (cases)
    w = p.events.workup_at_onset
    for concept in w.concepts:
        if concept not in p.measurements:
            raise ValueError(f"workup concept {concept!r} needs a measurements entry")
        spec = p.measurements[concept]
        who = np.flatnonzero(is_case & (rng.random(n) < w.probability))
        dist = spec.case or spec.control
        values = rng.normal(dist.mean, dist.sd, len(who))
        if spec.clip:
            values = np.clip(values, *spec.clip)
        rows.append(
            pd.DataFrame(
                {
                    "pi": who,
                    "domain": "measurement",
                    "logical_concept": concept,
                    "value_num": np.round(values, spec.decimals),
                    "unit_raw": spec.unit,
                    "start_time": anchor[who].astype("datetime64[ns]"),
                    "visit_id": anchor_visit.reindex(who).to_numpy(),
                }
            )
        )

    # ---------------------------------------------------------------- recipe and background events
    event_visits: dict[tuple[int, np.datetime64], str] = {}
    extra_visits: list[tuple[int, np.datetime64, str, str]] = []

    def visit_for(pi: int, day: np.datetime64, vtype: str) -> str:
        if day == anchor[pi]:
            return str(anchor_visit[pi])
        key = (pi, day)
        if key not in event_visits:
            vid = f"SYN-V-{pi + 1:06d}-E{len(event_visits) + 1:05d}"
            event_visits[key] = vid
            extra_visits.append((pi, day, vtype, vid))
        return event_visits[key]

    def emit(spec: EventSpec, eligible: NDArray[Any]) -> None:
        who = np.flatnonzero(eligible & (rng.random(n) < spec.probability))
        recs = []
        for off in spec.offsets_days:
            vals = (
                rng.normal(spec.value.mean, spec.value.sd, len(who))
                if spec.value is not None
                else np.full(len(who), np.nan)
            )
            for pi, v in zip(who, vals, strict=True):
                day = anchor[pi] + off * DAY
                if not (obs_start[pi] <= day <= obs_end[pi]):
                    continue
                recs.append((pi, day, v, visit_for(int(pi), day, spec.visit_type)))
        if recs:
            pi_, day_, val_, vid_ = zip(*recs, strict=True)
            rows.append(
                pd.DataFrame(
                    {
                        "pi": pi_,
                        "domain": spec.domain,
                        "logical_concept": spec.concept,
                        "value_num": np.round(np.array(val_, dtype=float), spec.decimals),
                        "unit_raw": spec.unit,
                        "start_time": np.array(day_, dtype="datetime64[ns]"),
                        "visit_id": vid_,
                    }
                )
            )

    ev = p.events
    for es in ev.case_recipe:
        emit(es, is_case)
    for es in ev.control_recipe:
        emit(es, ~is_case)
    for es in [*ev.background, *ev.exclusions]:
        group_mask = {"all": np.ones(n, bool), "case": is_case, "control": ~is_case}[es.group]
        emit(es, group_mask)

    # ---------------------------------------------------------------- background conditions
    for concept in sorted(p.conditions):
        c = p.conditions[concept]
        has = rng.random(n) < np.where(is_case, c.case_rate, c.control_rate)
        frac = rng.uniform(0, 1, n)
        end = anchor if c.timing == "before_anchor" else obs_end
        for pi in np.flatnonzero(has):
            day = obs_start[pi] + _days(frac[pi] * ((end[pi] - obs_start[pi]) / DAY))
            rows.append(
                pd.DataFrame(
                    {
                        "pi": [pi],
                        "domain": c.domain,
                        "logical_concept": concept,
                        "value_num": [np.nan],
                        "unit_raw": None,
                        "start_time": [np.datetime64(day, "ns")],
                        "visit_id": [
                            visit_for(int(pi), np.datetime64(day, "D"), vd.anchor_visit_type)
                        ],
                    }
                )
            )

    if extra_visits:
        pi_, day_, vt_, vid_ = zip(*extra_visits, strict=True)
        rows.append(
            pd.DataFrame(
                {
                    "pi": pi_,
                    "domain": "visit",
                    "logical_concept": vt_,
                    "value_num": np.nan,
                    "unit_raw": None,
                    "start_time": np.array(day_, dtype="datetime64[ns]"),
                    "visit_id": vid_,
                }
            )
        )

    obs = pd.concat([r for r in rows if len(r)], ignore_index=True)
    obs["person_id"] = pids[obs.pi.to_numpy(dtype=int)]
    obs["start_time"] = pd.to_datetime(obs.start_time)
    obs["end_time"] = pd.NaT
    obs["time_precision"] = "date"
    obs["value_concept"] = None
    obs["source_table"] = "synthetic_population"
    obs = obs.drop(columns="pi").sort_values(
        ["person_id", "start_time", "domain", "logical_concept", "visit_id"], kind="stable"
    )
    cols = [
        "person_id",
        "domain",
        "logical_concept",
        "value_num",
        "value_concept",
        "unit_raw",
        "start_time",
        "end_time",
        "time_precision",
        "visit_id",
        "source_table",
    ]
    return Population(persons, obs[cols].reset_index(drop=True), groups, p.seed)
