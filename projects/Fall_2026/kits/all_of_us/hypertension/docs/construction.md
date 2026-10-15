# Construction — Hypertension

## 1. Official documentation
2017 ACC/AHA high blood pressure guideline (`acc_aha_bp_2017`, tier 4; primary text not retrievable
automatically); Teixeira et al. 2017 (`teixeira_2017_htn`, tier 5); OMOP CDM v5.4 (tier 3).

## 2. Clinical / dataset definition
Current-state hypertension phenotype (FR-130). **[documentation]** ACC/AHA stage 1 threshold
≥ 130/80. **[PROVISIONAL]** two elevated readings on distinct days approximate "average of ≥ 2
readings on ≥ 2 occasions".

## 3. Logical concepts and dataset realizations
`htn_diagnosis`, `systolic_bp`, `diastolic_bp`, `antihypertensive_medications`,
`pregnancy_hypertension`, `secondary_hypertension`, plus revealer concepts; synthetic realizations
only; `omop` empty (V-23c, V-25).

## 4. Cohort, cases, and controls
**[PROVISIONAL]** Adults ≥ 18. Cases: systolic ≥ 130 on ≥ 2 days, or diastolic ≥ 80 on ≥ 2 days, or
≥ 2 diagnoses, or diagnosis + antihypertensive; no pregnancy-related hypertension in the prior year;
no secondary hypertension. Controls: ≥ 2 systolic < 130 and ≥ 2 diastolic < 80, no reading
≥ 140/90, no diagnosis, no antihypertensive. **[method decision]** matched sampling, 2 per case.

## 5. Index and cutoff rules
**[method decision]** Case index: first date the case rule holds. **[PROVISIONAL]** index day and
encounter excluded (same-visit vitals and labs); washout 0; 3-year lookback.

## 6. Features and exclusions
See [features](features.md).

## 7. Kit definition (configuration)
`kit.yaml`, `phenotype.yaml`; salt `aou_htn_current-s1`; seed 2301.

## 8. Notebook and baseline model
Generated Template A notebook with a logistic regression baseline in a visible `Pipeline`.
