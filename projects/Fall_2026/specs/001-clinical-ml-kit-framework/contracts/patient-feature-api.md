# Contract: Patient and Feature API

Two entry points with **identical semantics**, verified by tests on the golden patients:

1. **Patient view** (teaching/EDA; one patient): `CutoffView`
2. **Bulk builder** (training; whole cohort, vectorized): `FeatureMatrixBuilder`

## Patient view

```text
timeline = kit.patient(person_id)               # synthetic mode; in the Workbench, IDs stay in-session
view = timeline.as_of(index_time)               # uses the kit's TemporalPolicy; immutable
view.latest("creatinine")      -> Obs | Missing
view.previous("creatinine")    -> Obs | Missing
view.history("creatinine")     -> list[Obs]  (ascending, cutoff-filtered)
view.derive("creatinine", "delta" | "pct_change" | "mean" | "rolling_mean(P365D)" |
            "min" | "max" | "std" | "slope" | "count" | "time_since_last") -> Value | Missing
view.has_condition(logical_concept, within=None) -> bool
view.medication_history(logical_concept)        -> list[Exposure]
view.prior_visits(type=None, within=None)        -> list[Visit]
```

- `Obs` = {value, unit (canonical), time, domain, concept_id, source_table, mapping_version}.
- `Missing` = {reason: `no_observation | outside_lookback | excluded_by_policy | unit_rejected`}.
  It is a typed sentinel, never 0, never a "normal" value (FR-059).
- Asking for a prohibited or label-defining feature raises `ProhibitedFeatureError`.
- `slope` uses value per day over the lookback window via least squares and needs ≥2 points
  (otherwise `Missing`).
- `time_since_last` is measured in days from the effective cutoff.

## Bulk builder
`FeatureMatrixBuilder(kit).build(cohort_df) -> (X: DataFrame, lineage: DataFrame)`
- One column per (feature, derivation). Column names follow `<feature>__<derivation>`.
- `lineage` maps each non-missing cell to the max source `start_time` and `visit_id` used, so
  the leakage checker can verify the cutoff after the fact (R-12 step 3).
- Missing cells are NaN in `X`. Missingness indicators are added by Template A's preprocessing,
  not here.

## Golden-patient acceptance (from spec User Story 4)
Creatinine: 2025-01-01 = 0.9, 2025-06-01 = 1.0, 2026-01-01 = 1.2, 2026-03-01 = 1.5.
Index 2026-01-01 with `same_day: include`, washout 0:
latest = 1.2; previous = 1.0; delta = 0.2; count = 3; the 2026-03-01 value appears in no feature
or lineage row.
With `same_day: exclude_index_day`: latest = 1.0; previous = 0.9; delta = 0.1.
Both the patient view and the bulk builder must produce exactly these values.
