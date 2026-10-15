# Data Model: Clinical ML Kit Framework

**Date**: 2026-10-15 | **Plan**: [plan.md](plan.md)

Logical entities, fields, relationships, validation rules, and state transitions. Field types use
Python/Pydantic-style names. "FR-xxx" refers to [spec.md](spec.md). Concrete YAML and JSON
shapes are in [contracts/](contracts/).

---

## 1. Clinical data (adapter output; generic, dataset-independent)

### Person
| Field | Type | Rules |
|---|---|---|
| person_id | str | Opaque; unique per dataset. Never written to the repo for real data. |
| birth_date / birth_year | date \| int | Whichever the dataset provides; age is derived relative to the index time. |
| sex_at_birth | str \| None | Coded value from the dataset's vocabulary (mapping `VERIFY`); used only where the kit allows it. |
| demographics | dict[str, str \| None] | Other validated variables declared in the feature registry. |
| observation_start / observation_end | datetime \| None | Observation-window bounds when the dataset supports them (AoU `VERIFY`, V-11). |

### Observation (long format; one row per observation)
| Field | Type | Rules |
|---|---|---|
| person_id | str | FK → Person |
| domain | enum `measurement \| condition \| drug \| procedure \| visit \| observation \| survey \| device` | |
| concept_id | str | Source vocabulary concept identifier (string to support non-OMOP datasets) |
| feature_key | str \| None | Registry feature this row was mapped to (null = unmapped) |
| value_num | float \| None | |
| value_concept | str \| None | Categorical value |
| unit_raw | str \| None | As delivered by the source |
| unit | str \| None | Normalized canonical unit after registry conversion |
| start_time | datetime | Observation/event time used for cutoff logic |
| end_time | datetime \| None | For drug eras and visits |
| time_precision | enum `datetime \| date` | Date-only values are treated as end-of-day for same-day rules (R-12) |
| visit_id | str \| None | Links to the visit for index-encounter exclusion |
| source_table | str | e.g., OMOP `measurement` |
| mapping_version | str | Concept-set or registry version that produced `feature_key` |

**Validation**: `start_time` not null; `unit` must be in the registry's accepted units for
`feature_key` or the row is rejected with a logged reason (never silently coerced); values
outside the registry's plausible range are flagged (configurable: drop or keep with a flag), never
clamped.

### PatientTimeline / CutoffView
- `PatientTimeline` = Person + their Observations, ordered by `start_time`.
- `CutoffView` = `PatientTimeline.as_of(index_time, temporal_policy)`. It contains **only**
  observations permitted by the effective cutoff for each domain/concept set (R-12) and is
  immutable. All feature derivations take a `CutoffView`, never a raw timeline.

---

## 2. Definitions (versioned, provenance-bearing)

All definitions share: `id`, `version` (semver), `status` (§ 5), `provenance: list[ProvenanceRef]`,
`deviations: list[Deviation]`.

### SourceRecord (`definitions/sources/*.yaml`)
| Field | Type |
|---|---|
| source_id | str (slug) |
| title | str |
| organization | str |
| url_or_identifier | str |
| source_version / accessed_date | str \| None / date |
| priority_tier | int 1–6 (FR-150 hierarchy) |
| notes | str |

### ProvenanceRef (embedded on any definition item)
| Field | Type |
|---|---|
| source_id | FK → SourceRecord |
| locator | str (section, table, or page in the source) |
| application | str (how the source was applied) |
| verification_status | `draft \| requires_verification \| verified` |
| verified_by / verified_on | str \| None / date \| None (required when `verified`) |

### Deviation
| Field | Type |
|---|---|
| item | str (path of the deviating field) |
| official_definition | str |
| deviation | str |
| reason | str |
| expected_impact | str |

### LogicalConcept (`definitions/concepts/<logical_id>.yaml`)
The data-source-independent clinical meaning that kits, phenotypes, and the registry reference.
| Field | Type | Rules |
|---|---|---|
| logical_id | str | e.g., `t2d_diagnosis`, `creatinine` |
| version, status | semver, status | |
| description | str | Clinical meaning |
| domain | enum | |
| provenance | list[ProvenanceRef] | Supports the **clinical meaning** (tiers 1–6) |

### ConceptSetRealization (`definitions/concept_sets/<namespace>/<logical_id>/<version>.yaml`)
A dataset-specific realization of one LogicalConcept. The active adapter resolves logical ids
through its namespace.
| Field | Type | Rules |
|---|---|---|
| logical_id, version | — | FK → LogicalConcept |
| namespace | `omop \| synthetic` (later: per specialty dataset) | One per adapter vocabulary |
| status, provenance | — | Provenance supports the **mapping** (separate from clinical-meaning provenance) |
| domain | enum | Must equal LogicalConcept.domain and every member's domain |
| vocabulary | str | e.g., OMOP standard vocabulary; `synthetic` for the synthetic namespace |
| members | list[{concept_id, include_descendants: bool, exclude: bool}] | `omop`: **empty until verified**, no invented IDs (P-5). `synthetic`: fictional codes matching `^SYN-`, header "synthetic; not real OMOP concepts" |
| accepted_units | list[{unit, factor_to_canonical}] | Measurements only |
| canonical_unit | str \| None | |

Resolution rules: the All of Us adapter resolves only `omop` realizations with verified provenance
(below the `workbench` level it raises `PendingVerification`). The synthetic adapter resolves only
`synthetic` realizations. Neither adapter can resolve the other's namespace.

### FeatureRegistryEntry (`definitions/features/registry.yaml`)
| Field | Type | Rules |
|---|---|---|
| feature_key | str | e.g., `creatinine` |
| description | str | |
| domain | enum | |
| value_type | `numeric \| categorical \| boolean \| event` | |
| concept | LogicalConceptRef | Logical id + version; realizations per namespace live under `definitions/concept_sets/` |
| canonical_unit, plausible_range | str, (float, float) \| None | Range itself needs provenance |
| status, provenance | — | |

Traceability chain (FR-153): `feature_key → LogicalConcept (clinical provenance) →
ConceptSetRealization[namespace] (mapping provenance; domain, members, accepted_units) →
source_table → SourceRecord`, with `mapping_version` (realization version) stamped on each
Observation row.

### PhenotypeDefinition (`kits/<dataset>/<kit>/phenotype.yaml`)
| Field | Type | Rules |
|---|---|---|
| id, version, status, provenance, deviations | — | |
| case_rule | RuleExpr | Declarative (§ 3) |
| case_index_rule | IndexRule | e.g., "earliest date on which case_rule is satisfied" |
| control_rule | RuleExpr | Must include **positive control evidence**, not just absence (FR-132) |
| control_index_rule | IndexRule | One eligible index visit per control person, chosen per `control_sampling` |
| control_sampling | ControlSampling | See below |
| min_observation_history | Duration | Verified, provisional, or `UNVERIFIED` (contracts/kit-definition.md) |
| repeat_evidence | RuleExpr \| None | |
| label_defining_concepts | list[LogicalConceptRef] | Feeds the target-leakage check (R-13) |

### ControlSampling (in the phenotype definition)
| Field | Type | Rules |
|---|---|---|
| strategy | `all_eligible \| random_ratio \| matched` | No global default; each kit declares one |
| controls_per_case | float \| None | Required for `random_ratio` and `matched`; null for `all_eligible` |
| match_on | list[str] | Required for `matched` (e.g., attributes chosen in ADR-002, such as visit type or calendar year) |
| seed | int | Drives sampling reproducibly; recorded in the RunManifest |
| rationale, provenance | str, list[ProvenanceRef] | Required; value may be provisional (synthetic only) |

**Prevalence semantics**: the SplitManifest records the **sampled development prevalence**. It
differs from the **underlying population prevalence** whenever `strategy ≠ all_eligible`.
Probabilities from models trained or evaluated on a case-control sample are labeled
`probability_basis: development_sample` in the envelope, and are never presented as population
disease probabilities. Doing so would require a documented recalibration method (out of scope for
M1–4).

### VisitBiasCheck (optional, in the kit definition; ADR-002)
`utilization_features` (registry keys) and `max_utilization_auroc` (method decision). A
utilization-only logistic regression fitted on the training partition is scored on validation; an
AUROC above the bound is reported as index-visit bias.

### CohortDefinition
`inclusion: list[RuleExpr]`, `exclusion: list[RuleExpr]`, `eligible_period`, `age_range`, each
item with provenance.

### TemporalPolicy (in the kit definition)
| Field | Type | Rules |
|---|---|---|
| same_day | `include \| exclude_index_day` | **Required, no default**; verified, provisional, or `UNVERIFIED` |
| washout | Duration (≥ 0) | Gap before index that is excluded for all domains |
| exclude_index_encounter | bool | Required; no default |
| windowed_exclusions | list[{target: LogicalConceptRef \| domain, before: Duration, after: Duration, reason}] | Diagnostic-workup exclusions |
| lookback | Duration | Earliest observation window |

An observation `o` is permitted only if **all** hold:
1. Upper bound: with `same_day: include`, `o.start_time ≤ index_time − washout`; with
   `same_day: exclude_index_day`, `date(o.start_time) < date(index_time − washout)`. Date-only
   observations dated on the index day count as same-day.
2. `o.start_time ≥ index_time − lookback`.
3. If `exclude_index_encounter`: `o.visit_id ≠ index_visit_id`.
4. `o` does not fall in any `windowed_exclusions` window that matches its concept set or domain.
5. `o` is not in any label-defining logical concept (enforced separately for all times; R-13).

### KitDefinition (`kits/<dataset>/<kit>/kit.yaml`)
See [contracts/kit-definition.md](contracts/kit-definition.md) for all fields. Relationships:
one `dataset`, one `template_family`, one `PhenotypeDefinition`, one `CohortDefinition`, one
`TemporalPolicy`, N feature selections (each referencing a registry entry and a derivation), N
prohibited entries, and N provenance references.

---

## 3. RuleExpr (declarative rule language, deliberately small)

A tree of `all_of`, `any_of`, `not`, and leaf predicates:

- `has_event(concept, min_count, within: Duration?, distinct_days: bool, min_span: Duration?)`
- `measurement(concept, op: < ≤ > ≥, value, unit, min_count, within, distinct_days, min_span)` — `min_span`: first-to-last qualifying event span (chronicity; added in M4)
- `age_at_index(op, years)`
- `observation_history(min: Duration)`
- `visit(type_concept, min_count, within)`

(`concept` = logical concept id, resolved by the active adapter.)

Thresholds in leaves carry provenance. Kits needing a predicate not in this list must follow
the Constitution XXIII review (add a reusable predicate rather than kit code). The rule evaluator
lives in `cohort/` and runs only on adapter data.

---

## 4. Modeling and outputs

### KitData (returned by `kit.load()`)
`train: Dataset`, `validation: Dataset`, `test` (hidden; § R-11), `feature_spec`, `split_manifest`,
`run_manifest`. Each `Dataset` = `X: DataFrame`, `y: Series`, `index_times: Series`, `groups: Series`,
and `person_ids` (synthetic mode only).

**`groups`** (opaque patient grouping key; all execution modes):
- Value = SHA-256(`"group:" + split.salt + person_id`), truncated hex. It is stable for all rows of
  one person, distinct across persons (collisions checked at load), and deterministic, so grouped
  CV is reproducible.
- It is a pseudonymous, participant-derived value. Under the `all_of_us_workbench` policy it is
  never written outside the Workbench, never shown (the `Dataset` repr masks it), never a column of
  `X`, and never emitted in envelopes or completion records.
- For the test partition, groups are available only inside `kit.final_evaluation` (test guard).
- It is passed as `groups=` to the grouped splitter in every mode (synthetic and All of Us).

**One modeled row per person** (invariant for `binary_tabular` + `current_state`, i.e., all M4
reference kits): each person contributes exactly one (index time, label) row to the modeled data.
`kit.load()` raises `KitValidationError` if violated. A future template may relax this only by
declaring multi-row support explicitly.

**`min_features_present`**: applied in `kit.load()` **before** splitting, with the excluded count
logged (filtered per the V-03 rule when it leaves the Workbench).

### SplitManifest
`strategy: hash | official`, `salt`, `salt_version`, `kit_version`, `fractions`, `digest`,
`sampled_development_prevalence`, per-partition `{n, n_pos, prevalence}` (aggregates leaving the
Workbench follow the V-03 dissemination rule). No person IDs or group keys.

### RunManifest
Fields listed in research R-19. Content-hashed; embedded in completion records and model metadata.

### ModelHandle
Created by `kit.final_evaluation` / `kit.complete` around the student's fitted scikit-learn
estimator or Pipeline (built in visible notebook code). Fields: `model_id`, `model_version`,
`kit_id`, `template_family`, `estimator` (in-memory, the student's object), `threshold`,
`calibration_status`, `run_manifest`, `environment`.

### CompletionRecord (deliverable from any environment)
`model_id/version`, `kit_id`, kit-definition hash, phenotype version, environment, metrics
(validation + single test evaluation), calibration summary, explainability summary, run manifest,
`portable: bool`. Workbench records pass the dissemination filter defined by verification task
V-03 (threshold pending verification).

### SyntheticPopulationParams (`synthetic/generator_params/<kit_id>.yaml`)
Seeded generator settings for **end-to-end model and notebook execution** in synthetic mode.
(Golden fixtures in `synthetic/golden/` are separate and serve deterministic unit and edge tests.)
| Field | Type | Rules |
|---|---|---|
| header | {artificial: true, clinically_realistic: false, derived_from_participant_data: false, purpose: "framework testing and student workflow only; not a prevalence or effect-size simulation"} | Required; rejected otherwise |
| seed, n_persons | int, int | Reproducible |
| case_recipe / control_recipe | per logical concept: events, measurement values, timing relative to index, medications, visits | Must satisfy the kit's current verified or provisional rules using `SYN-` realizations only |
| planted_relationships | list[{predictor, effect, note}] | Artificial; documented; for non-label-defining predictors |
| missingness, visit_density | per feature / per person | Exercise missing values and temporal behavior |
Never fitted to, sampled from, or tuned against participant data; makes no attempt to reproduce
participant-level distributions.

### FR081Evidence (`kits/<dataset>/<kit>/evidence/fr081.yaml`)
Permitted/suppressed aggregates only (V-03 rule): eligible persons, positives, eligible controls,
class balance, required-feature availability, missingness/coverage per feature, longitudinal
coverage, CDR version, run date, checklist reference. Referenced by the catalog entry's `evaluation`.

### PredictionEnvelope
See [contracts/prediction-envelope.md](contracts/prediction-envelope.md).

### KitCatalogEntry (`kits/catalog.yaml`)
`candidate_id`, `name`, `dataset`, `status` (§ 5b), `decision_rationale`, `evaluation`
(FR-081/FR-082 checklist results with evidence links), `decided_on`, `reviewer`.

---

## 5. State transitions

### 5a. Definition and kit status (provenance-gated)
```
draft ──► requires_verification ──► verified ──► approved
  ▲              │                      │
  └──────────────┴──── (edit) ◄─────────┘   (any edit to a verified/approved item → requires_verification)
```
- `verified` (item): its provenance has ≥1 ref with `verification_status: verified` and a
  named verifier.
- Value states (verified / provisional / unverified) and validation levels (schema / synthetic /
  workbench / approval) are defined in contracts/kit-definition.md. A kit containing provisional
  or unverified required values can be at most `requires_verification`. It can run in synthetic
  mode (level `synthetic`) but not in the Workbench.
- Kit `approved` requires: the `approval` validation level (all required values verified, FR-158);
  FR-081/082 evaluation passed with an FR081Evidence record; all kit tests pass; documentation
  complete (FR-156, mechanical check); reviewer sign-off recorded.
- Validation **rejects** `status: verified|approved` when any required value is provisional or
  unverified.

### 5b. Catalog status
`candidate → {approved | revised | merged | postponed | replaced | rejected}`; `revised` and
`postponed` may return to `candidate`. Every transition requires `decision_rationale`.

### 5c. Model lifecycle
`trained (in env) → evaluated (validation) → final_evaluated (test, logged once) → completed
(CompletionRecord)`, then `→ serialized_portable` only if `DataEnvironmentPolicy.portable_artifacts`
is true (never for `all_of_us_workbench`).

---

## 6. Kit contents

A kit directory (`kits/<dataset>/<kit>/`) contains:
- `kit.yaml` (KitDefinition, including `synthetic_population`), `phenotype.yaml`, `verification.yaml` (notes only), `evidence/fr081.yaml`
  (V-03-permitted aggregates), references to logical concepts and sources
- `docs/` (KitDocs, § 7)
- `kit.ipynb`: a **generated, executable student notebook** with the visible Python ML workflow
  ([contracts/student-notebook.md](contracts/student-notebook.md))
- `tests/`: kit-specific tests

Kits contain **no duplicated framework infrastructure** (adapters, mapping, cohort, feature,
splitting, leakage, envelope, provenance, or completion logic). The notebook's Python code is
expected and required.

### StudentNotebook (generated)
| Field | Type | Rules |
|---|---|---|
| template_family | str | Selects the skeleton |
| sections | ordered list (0–12) | Fixed per template family |
| cells | list[{role: framework \| baseline \| student \| markdown, source}] | Every cell tagged |
| rendered_values | {features, baseline.params, threshold_rule, metrics} | Must equal `kit.yaml` |
| framework_cell_hashes | dict | Recorded in the RunManifest at run time |

## 7. KitDocs (fixed documentation set per kit)
`README.md` (overview + reviewer Q&A index, FR-156), `clinical_background.md`,
`construction.md` (step-by-step: documentation → definition → concept sets → cohort/target →
features → config → notebook), `features.md` (included/excluded with rationale and mapping
table), `limitations.md`, and `verification_log.md`, which is **generated, read-only**
(`ckit docs`). It is rendered from the authoritative structured records: inline ProvenanceRefs
(verification status), provisional/unverified value states, Deviations, and
`kits/<dataset>/<kit>/verification.yaml` (narrative notes and decision category per item path:
`documentation_derived | method_decision`; **no status fields**). CI fails on hand edits. Notebook
Markdown sections are generated from these files, so each fact has one source.

`README.md` must contain the 12 FR-156 reviewer questions as headings, each with a non-empty
answer containing at least one relative link that resolves to an existing file or anchor
(mechanically tested).
