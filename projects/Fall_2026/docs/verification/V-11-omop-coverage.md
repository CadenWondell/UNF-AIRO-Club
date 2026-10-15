# V-11 — Populated OMOP tables and fields in the current CDR

| Field | Value |
|---|---|
| Status | **UNRESOLVED** (all fields unknown) |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (automated source search) |
| Manual action required | From the CDR v8 data dictionary on the Support Hub (registered users) or inside the Workbench (aggregate checks only, per V-03), mark each row below populated/absent. |

## Sources consulted

| Source | Organization | URL | Version/date | Tier |
|---|---|---|---|---|
| OMOP CDM v5.4 documentation | OHDSI | https://ohdsi.github.io/CommonDataModel/cdm54.html | v5.4 | 3 |
| All of Us Data Browser (public aggregate browser; dynamic app, not machine-readable) | All of Us Research Program | https://databrowser.researchallofus.org/ | accessed 2026-10-15 | 1 |

OMOP CDM documentation defines the tables and fields but cannot establish what the All of Us CDR
populates. The All of Us CDR data dictionary was not retrievable by automated fetch.

## Table/field status

| Table | Field(s) | Status |
|---|---|---|
| person | person_id, year_of_birth, birth_datetime, gender_concept_id, sex_at_birth_concept_id | unknown |
| measurement | measurement_concept_id, measurement_datetime/date, value_as_number, unit_concept_id, unit_source_value, visit_occurrence_id | unknown |
| condition_occurrence | condition_concept_id, condition_start_date/datetime, visit_occurrence_id | unknown |
| drug_exposure | drug_concept_id, drug_exposure_start_date/datetime, drug_exposure_end_date | unknown |
| procedure_occurrence | procedure_concept_id, procedure_date/datetime | unknown |
| visit_occurrence | visit_occurrence_id, visit_concept_id, visit_start_date/datetime, visit_end_date | unknown |
| observation_period | observation_period_start_date, observation_period_end_date | unknown |

## Decision

No SQL is written (T126–T127 blocked). Minimum observation history in the reference kits is
expressed through the generic `observation_history` predicate, which in synthetic mode uses the
generator's observation window; its All of Us realization is pending this item.

## Affected sections

contracts/dataset-adapter.md; T126–T128; per-kit control definitions (min history).
