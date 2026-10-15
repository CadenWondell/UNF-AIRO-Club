# Hypertension — current-state phenotype inference (`aou_htn_current`)

> Educational/research use only. Not a clinically validated risk score, diagnosis, or treatment
> recommendation. Status: **requires_verification** — every clinical value is PROVISIONAL
> (synthetic-only) until reviewed; the kit cannot run on All of Us data yet.

## What is the clinical question?
Given information that does not define the phenotype, does the record currently meet the
hypertension phenotype? See [clinical background](clinical_background.md#the-phenotype-in-plain-language)
and [construction step 2](construction.md#2-clinical--dataset-definition).
## What official documentation was used?
The 2017 ACC/AHA high blood pressure guideline, Teixeira et al. 2017 (EHR hypertension phenotyping),
OMOP CDM v5.4; see [construction step 1](construction.md#1-official-documentation).
## How was the cohort created?
Adults (provisional ≥ 18) with ≥ 365 days of history; see [construction step 4](construction.md#4-cohort-cases-and-controls).
## How were positive labels (cases) created?
Elevated BP (≥ 130 systolic or ≥ 80 diastolic) on ≥ 2 days, ≥ 2 diagnoses, or diagnosis +
antihypertensive; never medication alone; see [construction step 4](construction.md#4-cohort-cases-and-controls).
## How were controls created?
≥ 2 normal readings, none ≥ 140/90, no diagnosis or antihypertensive, matched 2:1; see
[construction step 4](construction.md#4-cohort-cases-and-controls).
## What is the index (as-of) time?
First date the case rule holds; controls: one matched eligible visit. See
[construction step 5](construction.md#5-index-and-cutoff-rules).
## Which features are included?
See [features](features.md#included-features).
## Which features are deliberately excluded, and why?
See [features](features.md#excluded-features) and the [V-24 review](features.md#indirect-label-revealer-review-v-24).
## How do raw fields map to framework features?
See the [mapping trace](features.md#mapping-trace).
## Which decisions come directly from documentation?
BP categories (ACC/AHA); see [construction step 2](construction.md#2-clinical--dataset-definition).
## Which decisions are project-specific methodological choices?
See [construction step 5](construction.md#5-index-and-cutoff-rules) and [step 7](construction.md#7-kit-definition-configuration).
## Which items remain unverified?
All clinical values; see the [verification log](verification_log.md) and
[limitations](limitations.md#provisional-and-unverified-items).
