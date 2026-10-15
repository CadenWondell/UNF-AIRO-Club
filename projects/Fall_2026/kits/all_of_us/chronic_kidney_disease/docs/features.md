# Features — Chronic Kidney Disease (`aou_ckd_current`)

## Included features

| Feature | Derivations | Why it is allowed |
|---|---|---|
| `age`, `sex_at_birth` | latest | Demographic context |
| `systolic_bp` (latest, mean), `diastolic_bp` | | Hypertension is a CKD correlate, not part of this phenotype |
| `bmi` | latest | Cardiometabolic context |
| `hemoglobin` | latest | Anemia is a CKD correlate; allowed because the phenotype does not use it |
| `hba1c`, `glucose` | latest | Diabetes is a CKD cause; not phenotype-defining here |
| `ldl`, `hdl` | latest | Lipids |
| `albumin` (serum) | latest | Liver/nutrition panel; distinct from urine albumin |
| `potassium` | latest | Electrolyte; not used by the phenotype; index-day values excluded by the same-day rule |
| `outpatient_visits` | count (last 365 days) | Utilization; monitored by the index-visit-bias check |

## Excluded features

| Item | Reason | Decision source |
|---|---|---|
| `ckd_diagnosis`, `egfr`, `creatinine`, `urine_albumin_protein` | label-defining (earlier values too, FR-134) | FR-135, phenotype |
| `aki_diagnosis` | label-source (used to exclude transient decreases) | phenotype |
| `bun` | indirect revealer | V-24 review |
| `cystatin_c` | indirect revealer (GFR marker) | V-24 review |
| `dialysis_transplant` | cohort exclusion and revealer | V-24 review |
| `nephrology_visit` | indirect revealer | V-24 review |
| `kidney_specific_medications` | indirect revealer | V-24 review |

## Indirect label-revealer review (V-24)

| Category | Decision | Justification against the prediction question |
|---|---|---|
| BUN | **Exclude** | Filtration-dependent and reported with creatinine; reveals kidney function |
| Cystatin C | **Exclude** | Alternative GFR marker (KDIGO uses it for eGFRcr-cys) |
| Dialysis/transplant procedures | **Exclude** (also cohort exclusion) | Treatment of kidney failure; reveals the label |
| Nephrology visits | **Exclude** | Referral follows recognized kidney disease |
| Kidney-specific medications (phosphate binders, ESAs) | **Exclude** | Prescribed because of CKD |
| Potassium / bicarbonate | **Potassium allowed; bicarbonate not used** | Not in the phenotype; same-day exclusion removes workup draws; bicarbonate omitted to keep the feature set small |
| Anemia markers (hemoglobin) | **Allowed** | CKD correlate, not phenotype-defining (plan § 17.2) |

## Mapping trace

feature → logical concept → realization (synthetic now; `omop` empty until V-22c/V-25) → source table → SourceRecord.
