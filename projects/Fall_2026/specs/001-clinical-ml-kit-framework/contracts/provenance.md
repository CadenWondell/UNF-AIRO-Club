# Contract: Provenance, Sources, and Verification

Realizes spec FR-150–FR-158. Implemented in `clinical_ml_kits.provenance`; run by
`ckit validate` and in CI.

## Files
- `definitions/sources/<source_id>.yaml` — one SourceRecord per document (fields in
  data-model § 2).
- Provenance refs are embedded **inline next to the item they support** (concept sets, registry
  entries, phenotype rules, thresholds, temporal policy values, split rules).
- `kits/<dataset>/<kit>/verification.yaml` — narrative notes and decision category
  (`documentation_derived | method_decision`) keyed by item path. It holds **no status fields**;
  status lives only in inline ProvenanceRefs and value states.
- `kits/<dataset>/<kit>/docs/verification_log.md` — **generated, read-only** by `ckit docs`, from
  inline provenance, value states (verified/provisional/unverified), deviations, and
  `verification.yaml`. Provisional items carry the "PROVISIONAL — synthetic-only" banner. CI runs
  `ckit docs --check` and fails on any hand edit. There is exactly one editable source of truth for
  verification status: the structured YAML.
- Logical concepts (`definitions/concepts/`) carry **clinical-meaning** provenance; realizations
  (`definitions/concept_sets/<namespace>/`) carry **mapping** provenance. Both are required for
  `omop` realizations to be verified.

## ProvenanceRef shape
```yaml
provenance:
  - source_id: omop_cdm_measurement_table        # → definitions/sources/
    locator: "MEASUREMENT table, field value_as_number"
    application: "Defines the source table/field for lab values"
    verification_status: requires_verification    # draft | requires_verification | verified
    verified_by: null
    verified_on: null
```

## Automated checks
| ID | Check | Failure |
|---|---|---|
| P-1 | Every `source_id` resolves to a SourceRecord | error |
| P-2 | Every required item (list below) has ≥1 ProvenanceRef | error (or kit forced to `draft`) |
| P-3 | `verified` refs have `verified_by` and `verified_on` | error |
| P-4 | Kit `status: verified\|approved` ⇒ every required item verified; no provisional value and no `UNVERIFIED` sentinel anywhere | error |
| P-5 | `omop` realization `members` non-empty ⇒ the realization has a verified provenance ref; `synthetic` realizations must use `^SYN-` codes and the synthetic header | error |
| P-10 | Provisional values have `note` and `pending` (V-ID) | error |
| P-11 | `verification.yaml` contains no status fields; `verification_log.md` equals the generated output | error |
| P-6 | Deviation entries have all five fields | error |
| P-7 | Editing a verified item (content hash changed) without a new verification ⇒ status reverts to `requires_verification` | error in CI if not reverted |
| P-8 | Feature traceability chain resolves end to end for every kit feature (FR-153) | error |
| P-9 | Source priority: when a tier 5–6 source is used for an item, a note explains why tiers 1–4 were insufficient | warning |

**Required items** (per kit): cohort inclusion/exclusion, case rule, case index rule, control rule,
control index rule, control sampling, min observation history, repeat evidence, label-defining
concepts, every feature's logical concept and `omop` realization and units, plausible ranges,
temporal policy values, split rule (if official), known limitations.

## Content hashing
Each verified item stores `content_hash` (SHA-256 of its canonical YAML). P-7 compares
the current hash to the stored one, so a silent edit cannot keep a `verified` status.
