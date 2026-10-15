# Type 2 Diabetes — current-state phenotype inference (`aou_t2d_current`)

> Educational/research use only. Not a clinically validated risk score, diagnosis, or treatment
> recommendation. Status: **requires_verification** — every clinical value is PROVISIONAL
> (synthetic-only) until reviewed; the kit cannot run on All of Us data yet.

## What is the clinical question?
Given information that does not define the phenotype, does the record currently meet the T2D
phenotype? See [clinical background](clinical_background.md#the-phenotype-in-plain-language) and
[construction step 2](construction.md#2-clinical--dataset-definition).
## What official documentation was used?
ADA Standards of Care 2026 (Section 2), the eMERGE T2D algorithm, OMOP CDM v5.4, and the All of Us
dissemination policy; see [construction step 1](construction.md#1-official-documentation).
## How was the cohort created?
Adults (provisional age ≥ 18) with ≥ 365 days of history; see [construction step 4](construction.md#4-cohort-cases-and-controls).
## How were positive labels (cases) created?
Combinations of T2D diagnoses, diabetes medications, and HbA1c ≥ 6.5 % without type 1/other diabetes;
see [construction step 4](construction.md#4-cohort-cases-and-controls).
## How were controls created?
Positive non-diabetic evidence (HbA1c < 5.7 % or glucose < 100 mg/dL), no diabetes codes or drugs,
matched 2:1 on visit type and year; see [construction step 4](construction.md#4-cohort-cases-and-controls).
## What is the index (as-of) time?
Cases: first date the case rule holds. Controls: one matched eligible visit. See
[construction step 5](construction.md#5-index-and-cutoff-rules).
## Which features are included?
See [features](features.md#included-features).
## Which features are deliberately excluded, and why?
Label-defining items and indirect revealers; see [features](features.md#excluded-features) and the
[V-24 review](features.md#indirect-label-revealer-review-v-24).
## How do raw fields map to framework features?
See the [mapping trace](features.md#mapping-trace).
## Which decisions come directly from documentation?
See the steps marked [documentation] in [construction](construction.md#2-clinical--dataset-definition).
## Which decisions are project-specific methodological choices?
See [construction step 5](construction.md#5-index-and-cutoff-rules) and
[step 7](construction.md#7-kit-definition-configuration).
## Which items remain unverified?
All clinical values; see the generated [verification log](verification_log.md) and
[limitations](limitations.md#provisional-and-unverified-items).
