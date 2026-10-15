# Contract: Dataset Adapter

Implemented as a `typing.Protocol` in `clinical_ml_kits.data.adapter`. Generic framework code
depends only on this protocol; adapter packages are discovered through a registry keyed by
`dataset.id`. **No module outside `adapters/<name>/` may import adapter internals** (enforced by
an import-boundary test).

## Clinical adapter protocol (M2; used by tabular/longitudinal templates)

| Method | Returns | Contract |
|---|---|---|
| `metadata()` | `DatasetMetadata{id, version, environment, namespace, supports: set[str]}` | `version` is required; recorded in the run manifest; `namespace` selects concept-set realizations (`omop`, `synthetic`) |
| `resolve(logical_concept_ref)` | `ConceptSetRealization` | Resolves a logical concept through the adapter's namespace (data-model § 2). Raises `PendingVerification` if the realization is missing or (for `omop`) not verified; never resolves another namespace |
| `policy()` | `DataEnvironmentPolicy` | See below |
| `persons(person_ids=None)` | Person DataFrame | |
| `observations(domain, concepts, person_ids=None, before=None, after=None)` | Observation DataFrame (data-model § 1) | `concepts` are logical refs resolved via `resolve`; `before` is an exclusive upper bound; **an adapter MUST NOT return rows at or after `before`**. The concept filter is applied at the source |
| `visits(person_ids=None, before=None)` | Visit observations | Includes `visit_id`, type, and start/end |
| `index_candidates(rule)` | DataFrame[person_id, index_time, index_visit_id] | Evaluates an index rule's primitive queries; the rule logic itself stays in `cohort/` |

There are deliberately no "retrieve history" or cohort methods. History is derived generically
from `observations(..., before=cutoff)` plus `CutoffView`, and cohort logic is generic. This
keeps adapters thin (spec: do not over-generalize).

### DataEnvironmentPolicy
| Field | synthetic | public (per license) | all_of_us_workbench |
|---|---|---|---|
| participant_level | false | dataset-dependent | **true** |
| serialize_in_environment | true | true | true |
| portable_artifacts | true | license-dependent | **false** |
| aggregate dissemination rule | none | none | Small-count dissemination threshold and scope: **pending verification task V-03** (no value in the architecture) |
| required validation level | `synthetic` | `synthetic` | `workbench` (no provisional values) |
| allow_write_paths | any | any | workspace only; refuses paths inside the git checkout |

The completion layer, not the notebook, enforces this policy.

## Adapters planned in detail (M2)

### `synthetic_clinical`
- Two backends: (a) **population** (default for `data_source="synthetic"`): the seeded generator
  driven by the kit's `synthetic_population` params, used for end-to-end model and notebook
  execution; (b) **golden**: hand-authored fixtures, used only by unit and edge tests (R-18). Kits
  never run notebooks on golden fixtures.
- Namespace `synthetic`: resolves logical concepts to fictional `SYN-` codes from
  `definitions/concept_sets/synthetic/`. These are explicitly not real OMOP concepts.
- Exact cutoff semantics are identical to the AoU adapter; it implements the same pushdown
  filters in pandas.
- Passes the shared adapter contract test suite (`tests/contract/test_adapter_contract.py`), run
  against every registered adapter.

### `all_of_us` (boundary only in M2; real queries validated in the Workbench in M4)
- Lives in `adapters/all_of_us/`; requires the `[aou]` extra.
- `__init__` verifies Workbench environment markers (V-10) and otherwise raises
  `EnvironmentNotPermitted`.
- Namespace `omop`: resolves logical concepts only to **verified** `omop` realizations.
- Translates resolved realizations → parameterized SQL over OMOP tables (`person`, `measurement`,
  `condition_occurrence`, `drug_exposure`, `procedure_occurrence`, `visit_occurrence`, plus
  `observation_period` if populated — V-11). Pushes down concept, person, and time filters.
- Normalizes units via registry `accepted_units`; rows with unaccepted units are rejected and
  counted (counts leaving the Workbench follow the V-03 rule).
- Never writes to disk except via the completion layer; no CSV dumps.
- Contract tests run in CI against a **mock query backend** that returns synthetic OMOP-shaped
  rows, so SQL generation and cutoff filters are tested without real data. Live verification is a
  manual checklist run inside the Workbench (quickstart § 4).

## Specialty adapters (interface direction only; M11)
A sibling protocol `SampleAdapter` for sample-centric datasets (signals, images, volumes):
`metadata()`, `policy()`, `samples(split=None) → DataFrame[sample_id, patient_key, label_cols…,
path_or_array_ref]`, `load(sample_id)`, `official_split()` (optional). Splitting reuses the same
hash-on-`patient_key` routine. Detailed design is deferred.
