# Contract: Kit Definition (`kit.yaml`)

**Format**: YAML, validated by Pydantic models (`clinical_ml_kits.core.kit_schema`); JSON Schema is
generated to `docs/schemas/kit-definition.schema.json`. **Schema version**: `kit_schema: 1.0`.

Validation fails loudly (non-zero exit / exception naming the field) on any rule below.

## Clinical value states (verified vs provisional)

Every clinically meaningful configurable value — thresholds, durations, temporal-policy choices,
control-sampling parameters, minimum history, repeat-evidence rules, and the realizations of
logical concept sets — is in exactly one of three states:

| State | YAML form | Meaning | Allowed in |
|---|---|---|---|
| **verified** | plain value with a `verified` ProvenanceRef | Sourced and verified (FR-150–158) | All validation levels |
| **provisional** | `{provisional: <concrete value>, note: "<why; not an approved clinical rule>", pending: <V-ID>}` | Concrete value chosen **only** so synthetic fixtures and notebooks can run. It is not an approved or official clinical rule | `schema`, `synthetic` levels only |
| **unverified** | `UNVERIFIED` sentinel | No value yet | `schema` level only |

Rules for provisional values:
- `note` and `pending` are required. A note must state that the value is for synthetic execution
  and testing and is not an approved clinical rule.
- A kit containing any provisional or unverified required value cannot have `status: verified` or
  `approved` (FR-158). It stays `draft` or `requires_verification`.
- Provisional values are never used for All of Us Workbench execution: `load_kit(...,
  data_source="all_of_us")` requires the `workbench` level.
- Generated docs and notebooks render every provisional value with the banner "PROVISIONAL —
  synthetic-only, not an approved clinical definition", and the generated verification log lists
  them (contracts/provenance.md).

## Validation levels

`ckit validate --level {schema|synthetic|workbench|approval}`; `load_kit` checks the level its
data source requires.

| Level | Passes when | Required for |
|---|---|---|
| `schema` | Structure and cross-field rules valid; sentinels allowed | Any commit (CI) |
| `synthetic` | No `UNVERIFIED` in any value needed to execute; provisional allowed; every logical concept set has a synthetic realization; `synthetic_population` params exist and validate | Synthetic notebook generation and execution, CI kit tests |
| `workbench` | No provisional or `UNVERIFIED` required values; every logical concept set used has a verified `omop` realization | `data_source="all_of_us"`; Workbench verification run |
| `approval` | `workbench`, plus all approval conditions (data-model § 5a), including the FR-081 evidence record | `status: approved` |

## Fields

| Field | Required | Type / values | Validation |
|---|---|---|---|
| kit_schema | yes | `"1.0"` | |
| kit_id | yes | slug, e.g. `aou_t2d_current` | Unique in the catalog |
| name | yes | str | |
| kit_version | yes | semver | |
| status | yes | `draft \| requires_verification \| verified \| approved` | `verified`/`approved` rejected if any required value is provisional or unverified (FR-158) |
| dataset | yes | `{id, version}` | `id` must have a registered adapter; `version` may be provisional or unverified below `workbench` |
| template_family | yes | `binary_tabular` (M1–4) | Must be a registered template |
| clinical_question | yes | str | |
| prediction_type | yes | `current_state \| future_risk` | |
| horizon | conditional | ISO-8601 duration | Required iff `future_risk`; **must be absent** for `current_state` |
| phenotype | yes | path + version → PhenotypeDefinition | Version must exist; includes `control_sampling` (data-model § 2) |
| cohort | yes | CohortDefinition (inline or path) | |
| temporal_policy | yes | TemporalPolicy | `same_day` and `exclude_index_encounter` have **no default**: each must be present as verified, provisional, or `UNVERIFIED` |
| features | yes | list[{feature: registry key, derivations: [latest, previous, delta, pct_change, mean, rolling_mean(window), min, max, std, slope, count, time_since_last], window?}] | Every key exists in the registry |
| prohibited | yes (may be empty) | list[{feature \| concept (logical id) \| domain, reason}] | ∩ features = ∅ unless `justified_inclusions` |
| justified_inclusions | no | list[{item, rationale, provenance}] | |
| leakage_risks | yes | list[{description, mitigation}] | |
| missingness | yes | {strategy: `median_impute_with_indicator` (Template A default), min_features_present?: int} | `min_features_present` is applied at load time, before splitting |
| baseline | yes | {model: `logistic_regression`, params: {C, penalty, class_weight, max_iter}} | Params from an allow-list |
| threshold_rule | yes | `youden \| max_f1 \| fixed(value)` (picked on validation) | |
| metrics | yes | list from {auroc, auprc, sensitivity, specificity, precision, recall, f1, confusion_matrix, brier} | Must include ≥1 imbalance-aware metric (auprc or f1/precision-recall) |
| calibration | yes | {required: bool, bins: int, strategy: `quantile \| uniform`, method: `none \| grouped_oof_sigmoid \| grouped_oof_isotonic \| grouped_native_sigmoid \| grouped_native_isotonic`} | `required: true` when outputs are risk probabilities. `grouped_oof_*` = framework out-of-fold helper (always available). `grouped_native_*` is **valid only if** the V-14 SourceRecord is verified and lists the running scikit-learn version as safely propagating groups; otherwise validation fails with `PendingVerification("V-14")`. Ungrouped calibration is never permitted |
| explainability | yes | {coefficients: bool, permutation_importance: bool} | |
| split | yes | {strategy: `hash \| official`, fractions, salt, salt_version, salt_history: list[{salt_version, reason, changed_on, kit_version}], min_positives_per_partition, prevalence_tolerance} | `salt` is fixed per kit; changing it requires incrementing `salt_version`, adding a `salt_history` entry with a documented reason, and bumping `kit_version`. Changing the salt to improve outcome balance is not an acceptable reason |
| seed | yes | int | |
| synthetic_population | yes (`synthetic` level and above) | path `synthetic/generator_params/<kit_id>.yaml` | Must exist, carry the artificial header, and yield cases and controls with ≥ `min_positives_per_partition` positives per partition (data-model § 4) |
| sources | yes | list[ProvenanceRef] | See [provenance.md](provenance.md) |
| known_limitations | yes | list[str] | Must include the sampled-vs-population prevalence limitation when `control_sampling.strategy ≠ all_eligible` |
| docs | yes | path to KitDocs folder | All six files present (data-model § 7) |

## Cross-field rules
1. `features` ∩ (`prohibited` ∪ registry features whose logical concept is in
   `phenotype.label_defining_concepts`) = ∅, unless listed in `justified_inclusions`.
2. Every threshold, duration, concept, and sampling parameter used anywhere has a `ProvenanceRef`
   (verified) or a provisional `pending` reference; missing → status is forced to `draft`.
3. `prediction_type: current_state` ⇒ no `horizon`; `future_risk` ⇒ `horizon` plus an outcome window
   in the phenotype.
4. `template_family` must support `prediction_type` and the requested derivations. For
   `binary_tabular` with `current_state`, the **one modeled row per person** invariant applies
   (data-model § 4).
5. Kits reference **logical** concept ids (`t2d_diagnosis`), never data-source-specific
   realizations (`omop/...`, `synthetic/...`).

## Illustrative skeleton (T2D, M4) — placeholder values, not definitions

```yaml
kit_schema: "1.0"
kit_id: aou_t2d_current
name: "Type 2 Diabetes — current-state phenotype inference"
kit_version: 0.1.0
status: requires_verification
dataset: {id: all_of_us, version: UNVERIFIED}            # CDR version — V-10
template_family: binary_tabular
clinical_question: >
  Given clinical information that does not define the phenotype, does the patient's record
  currently meet the validated T2D phenotype?
prediction_type: current_state
phenotype: {path: phenotype.yaml, version: 0.1.0}        # contains control_sampling
temporal_policy:
  same_day:
    provisional: exclude_index_day
    note: "Synthetic execution/testing only; not an approved clinical rule."
    pending: V-20
  exclude_index_encounter:
    provisional: true
    note: "Synthetic execution/testing only; not an approved clinical rule."
    pending: V-20
  washout: UNVERIFIED            # must become provisional or verified before the synthetic level passes
  lookback: UNVERIFIED
  windowed_exclusions: []
features:
  - {feature: bmi, derivations: [latest, delta]}
  - {feature: systolic_bp, derivations: [latest, mean]}
prohibited:
  - {concept: t2d_diagnosis, reason: label-defining}
  - {feature: hba1c, reason: label-defining}
  - {feature: glucose, reason: label-defining}
  - {concept: diabetes_medications, reason: label-defining}
split: {strategy: hash, fractions: [0.70, 0.15, 0.15], salt: "aou_t2d_current-s1", salt_version: 1, salt_history: [], min_positives_per_partition: 10, prevalence_tolerance: 0.05}   # methodological choices, documented as method decisions
# … remaining fields per table above
```
