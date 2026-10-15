"""Control sampling (R-25): all_eligible, random_ratio, matched; one index row per control."""

from __future__ import annotations

import numpy as np
import pandas as pd

from clinical_ml_kits.core.values import resolve

ATTRS = ("visit_type", "calendar_year", "sex_at_birth", "age_band")


def _one_visit_per_person(visits: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    shuffled = visits.iloc[rng.permutation(len(visits))]
    return shuffled.groupby("person_id", sort=True).head(1).sort_values("person_id")


def sample_controls(
    cases: pd.DataFrame, eligible: pd.DataFrame, sampling: object
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Pick controls from ``eligible`` (one row per eligible control *visit*).

    Returns one row per selected control person plus counts. ``eligible`` and ``cases`` carry the
    matching attributes in ``ATTRS``.
    """
    strategy = sampling.strategy  # type: ignore[attr-defined]
    rng = np.random.default_rng(sampling.seed)  # type: ignore[attr-defined]
    eligible = eligible.sort_values(["person_id", "index_time", "index_visit_id"]).reset_index(
        drop=True
    )
    counts = {"eligible_controls": int(eligible.person_id.nunique()), "unmatched_cases": 0}
    if strategy == "all_eligible":
        return _one_visit_per_person(eligible, rng).assign(matched_case=None), counts
    ratio = float(resolve(sampling.controls_per_case))  # type: ignore[attr-defined]
    if strategy == "random_ratio":
        persons = np.array(sorted(eligible.person_id.unique()), dtype=object)
        k = min(round(ratio * len(cases)), len(persons))
        chosen = set(rng.choice(persons, size=k, replace=False)) if k else set()
        pool = eligible[eligible.person_id.isin(chosen)]
        return _one_visit_per_person(pool, rng).assign(matched_case=None), counts
    if strategy == "matched":
        keys = list(sampling.match_on)  # type: ignore[attr-defined]
        per_case = max(1, round(ratio))
        groups = {k: g for k, g in eligible.groupby(keys, sort=True)}
        used: set[str] = set()
        picked: list[pd.Series] = []
        order = rng.permutation(sorted(cases.person_id))
        case_attrs = cases.set_index("person_id")
        for cid in order:
            key = tuple(case_attrs.loc[cid, keys])
            g = groups.get(key if len(keys) > 1 else key[0])
            if g is None:
                counts["unmatched_cases"] += 1
                continue
            avail = sorted(set(g.person_id) - used)
            if not avail:
                counts["unmatched_cases"] += 1
                continue
            take = rng.choice(
                np.array(avail, dtype=object), size=min(per_case, len(avail)), replace=False
            )
            for pid in sorted(take):
                rows = g[g.person_id == pid]
                row = rows.iloc[int(rng.integers(len(rows)))].copy()
                row["matched_case"] = cid
                picked.append(row)
                used.add(pid)
        out = pd.DataFrame(picked) if picked else eligible.head(0).assign(matched_case=None)
        return out.sort_values("person_id").reset_index(drop=True), counts
    raise ValueError(f"unknown control sampling strategy {strategy!r}")
