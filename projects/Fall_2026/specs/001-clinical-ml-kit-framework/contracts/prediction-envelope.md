# Contract: Prediction Envelope

**contract_version**: `1.0.0` (semver: additive optional field → MINOR; removal, rename, or
semantic change → MAJOR). Implemented as a Pydantic model; JSON Schema generated to
`docs/schemas/prediction-envelope.schema.json`. Realizes spec FR-090–FR-094.

One envelope = one prediction for one subject at one as-of time from one model.

## Fields

| Field | Presence | Type | Notes |
|---|---|---|---|
| contract_version | required | str semver | |
| kit_id | required | str | |
| model_id | required | str | |
| model_version | required | str semver | |
| target | required | {code: str, label: str} | e.g. `{code: t2d_phenotype, label: "Type 2 diabetes phenotype"}` |
| prediction_type | required | `current_state \| future_risk` | |
| as_of | required | ISO-8601 datetime with offset | Index time |
| horizon | conditional | ISO-8601 duration \| null | **Must be null** for `current_state`; required for `future_risk` |
| dataset | required | {id: str, version: str} | |
| definition_versions | required | {phenotype: str, cohort: str, kit: str, feature_registry: str} | |
| data_environment | required | `synthetic \| public \| all_of_us_workbench` | |
| subject_ref | required | str | Opaque. Synthetic/demo IDs only outside the Workbench |
| payload | required | discriminated union on `payload_type` | See below |
| calibration_status | conditional | `not_assessed \| assessed \| recalibrated` | Required when the kit declares calibration |
| explanation | optional | {method: str, top_features: list[{feature, contribution: float, value: float \| str \| null}]} | |
| input_metadata | optional | {features_present: int, features_missing: list[str]} | |
| model_metadata | optional | {template_family, trained_on_environment, run_manifest_hash, created_at} | |
| disclaimer | required | const str | "Educational/research output. Not a clinically validated risk score, diagnosis, or treatment recommendation." (FR-112) |

## Payloads
| payload_type | Fields | Milestone |
|---|---|---|
| `binary_probability` | probability: float [0,1]; threshold: float; predicted_class: 0\|1 \| null; **probability_basis**: `development_sample` (required; M1–4 only allows this value, meaning probability reflects the kit's sampled development prevalence, not population prevalence) | M1–4 |
| `binary_score` | score: float; threshold: float \| null; predicted_class \| null | reserved (non-probabilistic) |
| `multiclass_probability` | class_probabilities: dict[str, float] (sums to 1 ± 1e-6); predicted_class | M6 (reserved) |
| `survival`, `segmentation`, `detection`, `signal` | **not defined** | later; MINOR bump |

Unknown `payload_type` values are rejected by v1.0 validators. Consumers MUST NOT compare
`probability` across envelopes with different `target`, `prediction_type`, or `horizon` (FR-025).

## Example (current-state, synthetic)
```json
{
  "contract_version": "1.0.0",
  "kit_id": "aou_t2d_current",
  "model_id": "aou_t2d_current.baseline_lr",
  "model_version": "0.1.0",
  "target": {"code": "t2d_phenotype", "label": "Type 2 diabetes phenotype"},
  "prediction_type": "current_state",
  "as_of": "2026-01-01T00:00:00+00:00",
  "horizon": null,
  "dataset": {"id": "synthetic_clinical", "version": "0.1.0"},
  "definition_versions": {"phenotype": "0.1.0", "cohort": "0.1.0", "kit": "0.1.0", "feature_registry": "0.1.0"},
  "data_environment": "synthetic",
  "subject_ref": "SYN-000042",
  "payload": {"payload_type": "binary_probability", "probability": 0.31, "threshold": 0.27, "predicted_class": 1, "probability_basis": "development_sample"},
  "calibration_status": "assessed",
  "disclaimer": "Educational/research output. Not a clinically validated risk score, diagnosis, or treatment recommendation."
}
```

## Validation rules (tested in `tests/contract/`)
1. Every required field is present; `horizon` is null iff `current_state`.
2. `probability ∈ [0,1]`; `predicted_class` is consistent with `probability ≥ threshold`.
3. `data_environment: all_of_us_workbench` envelopes are never written outside the Workbench
   (enforced by the completion layer, not just by the schema).
4. Round-trip: model → envelope → JSON → envelope preserves equality.
5. No envelope field contains a person ID or group key; `subject_ref` is a separate opaque
   reference (synthetic IDs outside the Workbench).
6. `probability_basis` is present on `binary_probability` payloads.
