# Construction — Chronic Kidney Disease

## 1. Official documentation
KDIGO 2024 CKD guideline (`kdigo_ckd_2024`, tier 4; definition and Table 1 extracted from the
official PDF); 2021 CKD-EPI equation (`ckd_epi_2021`, tier 5); eMERGE CKD algorithm, Nadkarni 2014
(`nadkarni_2014_emerge_ckd`, tier 5); OMOP CDM v5.4 (tier 3).

## 2. Clinical / dataset definition
Current-state CKD phenotype (FR-130). **[documentation]** KDIGO: GFR < 60 or ACR ≥ 30 mg/g for
≥ 3 months. **[PROVISIONAL]** operationalization: two qualifying values on distinct days spanning
≥ 90 days.

## 3. Logical concepts and dataset realizations
`ckd_diagnosis`, `egfr`, `creatinine`, `urine_albumin_protein`, `aki_diagnosis`,
`dialysis_transplant`, plus revealer concepts. Synthetic realizations only; `omop` empty (V-22c,
V-25). eGFR is taken from the source measurement (equation to be checked in the CDR).

## 4. Cohort, cases, and controls
**[PROVISIONAL]** Adults ≥ 18; dialysis/transplant excluded. Cases: eGFR < 60 (≥ 2 days, span
≥ 90 days) or ACR ≥ 30 mg/g (same) or ≥ 2 CKD diagnoses, and no AKI in the prior 90 days. Controls:
≥ 2 eGFR ≥ 60, never < 60, no albuminuria, no CKD diagnosis. ≥ 365 days of history.
**[method decision]** matched sampling, 2 per case (ADR-002).

## 5. Index and cutoff rules
**[method decision]** Case index: the date chronicity is first satisfied. **[PROVISIONAL]** index
day and encounter excluded (the confirming draw usually comes with a metabolic panel and CBC);
washout 0; 3-year lookback.

## 6. Features and exclusions
See [features](features.md).

## 7. Kit definition (configuration)
`kit.yaml`, `phenotype.yaml`; chronicity via the reusable `min_span` predicate option (added in M4
instead of kit code); salt `aou_ckd_current-s1`; seed 2201.

## 8. Notebook and baseline model
Generated Template A notebook with a logistic regression baseline in a visible `Pipeline`.
