# Construction — Type 2 Diabetes

Each step is marked **[documentation]**, **[method decision]**, **[PROVISIONAL]**, or **[deviation]**.

## 1. Official documentation
ADA Standards of Care in Diabetes—2026, Section 2 (`ada_soc_2026_s2`, tier 4); eMERGE T2D EHR
algorithm, Kho et al. 2012 (`kho_2012_emerge_t2d`, tier 5); OMOP CDM v5.4 (`ohdsi_omop_cdm_v54`,
tier 3); All of Us Data and Statistics Dissemination Policy (`aou_dissemination_policy`, tier 1).
Primary ADA text could not be retrieved automatically; criteria are provisional until a reviewer
confirms them.

## 2. Clinical / dataset definition
Current-state T2D phenotype (FR-130): the record is consistent with T2D at the index time.
**[documentation]** structure from eMERGE; **[PROVISIONAL]** thresholds (HbA1c ≥ 6.5 %, two
distinct-day diagnoses).

## 3. Logical concepts and dataset realizations
`t2d_diagnosis`, `t1d_other_diabetes`, `diabetes_medications`, `hba1c`, `glucose`, plus revealer
concepts. Synthetic `SYN-` realizations exist; `omop` realizations are **empty** until verified
(V-21c, V-25).

## 4. Cohort, cases, and controls
**[PROVISIONAL]** Adults ≥ 18. Cases: any of (≥ 2 T2D diagnoses on distinct days; diagnosis +
medication; diagnosis + HbA1c ≥ 6.5 %; medication + HbA1c ≥ 6.5 %) and no type 1/other diabetes.
Controls: HbA1c < 5.7 % or glucose < 100 mg/dL, and no diabetes diagnosis, medication, or type 1/
other code (prediabetes excluded from controls). ≥ 365 days of history for everyone.
**[method decision]** matched control sampling (ADR-002), 2 per case.

## 5. Index and cutoff rules
**[method decision]** Case index: first date the case rule holds. Control index: one eligible
visit matched on visit type and calendar year. **[PROVISIONAL]** index day and index encounter
excluded; washout 0 days; 3-year lookback (V-20).

## 6. Features and exclusions
See [features](features.md). Label-defining concepts and indirect revealers are prohibited.

## 7. Kit definition (configuration)
`kit.yaml` and `phenotype.yaml` hold every rule; split salt `aou_t2d_current-s1`; seed 2101.
**[method decision]** threshold rule `youden`; AUPRC reported with prevalence.

## 8. Notebook and baseline model
Generated Template A notebook (`kit.ipynb`): logistic regression baseline in a visible scikit-learn
`Pipeline`, grouped tuning, grouped calibration, single logged test evaluation.
