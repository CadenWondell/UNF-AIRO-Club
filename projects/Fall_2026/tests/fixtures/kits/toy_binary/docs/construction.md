# Construction — toy binary kit
## 1. Official documentation
None. Toy kit for framework tests only.
## 2. Clinical / dataset definition
A fictional phenotype defined by fictional `SYN-FX-` codes. **[PROVISIONAL]**
## 3. Logical concepts and dataset realizations
`fx_*` fixture concepts with synthetic realizations only.
## 4. Cohort, cases, and controls
Age ≥ 18 (provisional); cases: two `fx_dx` on distinct days; controls: `fx_marker` < 5 and no `fx_dx`, two per case (random ratio). **[PROVISIONAL]**
## 5. Index and cutoff rules
Case index: date the case rule is first met. Control index: one outpatient visit. Index-day observations and the index encounter excluded. **[PROVISIONAL]**
## 6. Features and exclusions
See [features](features.md).
## 7. Kit definition (configuration)
`kit.yaml` **[method decision]**.
## 8. Notebook and baseline model
Generated Template A notebook; logistic regression baseline.
