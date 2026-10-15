# Chronic Kidney Disease — current-state phenotype inference (`aou_ckd_current`)

> Educational/research use only. Not a clinically validated risk score, diagnosis, or treatment
> recommendation. Status: **requires_verification** — every clinical value is PROVISIONAL
> (synthetic-only) until reviewed; the kit cannot run on All of Us data yet.

## What is the clinical question?
Given information that does not define the phenotype, does the record currently meet the CKD
phenotype? See [clinical background](clinical_background.md#the-phenotype-in-plain-language) and
[construction step 2](construction.md#2-clinical--dataset-definition).
## What official documentation was used?
KDIGO 2024 CKD guideline, the 2021 CKD-EPI equation paper, the eMERGE CKD algorithm, OMOP CDM v5.4;
see [construction step 1](construction.md#1-official-documentation).
## How was the cohort created?
Adults (provisional ≥ 18) with ≥ 365 days of history and no dialysis/transplant; see
[construction step 4](construction.md#4-cohort-cases-and-controls).
## How were positive labels (cases) created?
eGFR < 60 or ACR ≥ 30 mg/g on ≥ 2 days spanning ≥ 90 days, or ≥ 2 CKD diagnoses, without AKI in the
prior 90 days; see [construction step 4](construction.md#4-cohort-cases-and-controls).
## How were controls created?
Repeated normal eGFR (≥ 2 values ≥ 60), never < 60, no albuminuria or CKD code, matched 2:1; see
[construction step 4](construction.md#4-cohort-cases-and-controls).
## What is the index (as-of) time?
The date chronicity is first satisfied; controls: one matched eligible visit. See
[construction step 5](construction.md#5-index-and-cutoff-rules).
## Which features are included?
See [features](features.md#included-features).
## Which features are deliberately excluded, and why?
See [features](features.md#excluded-features) and the [V-24 review](features.md#indirect-label-revealer-review-v-24).
## How do raw fields map to framework features?
See the [mapping trace](features.md#mapping-trace).
## Which decisions come directly from documentation?
The CKD definition and thresholds (KDIGO); see [construction step 2](construction.md#2-clinical--dataset-definition).
## Which decisions are project-specific methodological choices?
See [construction step 5](construction.md#5-index-and-cutoff-rules) and [step 7](construction.md#7-kit-definition-configuration).
## Which items remain unverified?
All clinical values; see the [verification log](verification_log.md) and
[limitations](limitations.md#provisional-and-unverified-items).
