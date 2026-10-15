# Features — Type 2 Diabetes (`aou_t2d_current`)

## Included features

| Feature | Derivations | Logical concept | Why it is allowed |
|---|---|---|---|
| `age` | latest | `age` | Demographic risk context, not phenotype evidence |
| `sex_at_birth` | latest | `sex_at_birth` | Demographic context |
| `bmi` | latest, delta, mean | `bmi` | Adiposity is associated with T2D but does not define it |
| `weight` | latest | `weight` | As above |
| `systolic_bp`, `diastolic_bp` | latest (+ mean for systolic) | BP | Cardiometabolic context |
| `ldl`, `hdl`, `triglycerides` | latest | lipids | Dyslipidemia co-occurs with T2D; not part of the phenotype |
| `creatinine` | latest | `creatinine` | Renal function context |
| `alt` | latest | `alt` | Liver panel (fatty-liver association) |
| `hemoglobin` | latest | `hemoglobin` | Hematology context (also affects HbA1c reliability, not a revealer) |
| `outpatient_visits` | count (last 365 days) | `visit_outpatient` | Utilization; monitored by the index-visit-bias check |

## Excluded features

| Item | Reason | Decision source |
|---|---|---|
| `t2d_diagnosis` | label-defining (case evidence) | FR-135, phenotype |
| `t1d_other_diabetes` | label-defining (exclusion evidence) | phenotype |
| `diabetes_medications` | label-defining (case evidence) | FR-135, phenotype |
| `hba1c`, `glucose` | label-defining (case and control evidence); earlier values also excluded (FR-134) | FR-135, phenotype |
| `diabetic_complications` | indirect label revealer (see review) | V-24 review |
| `glucose_monitoring` | indirect label revealer | V-24 review |
| `diabetes_education` | indirect label revealer | V-24 review |

## Indirect label-revealer review (V-24)

| Category | Decision | Justification against the prediction question |
|---|---|---|
| Diabetic complication diagnoses (retinopathy, neuropathy, nephropathy) | **Exclude** | They are coded almost only in people already diagnosed with diabetes, so they reveal the label rather than inform an independent current-state inference |
| Glucose-monitoring supplies and procedures | **Exclude** | Ordered because of diagnosed diabetes; a direct proxy for the label |
| Diabetes education visits | **Exclude** | Occur after diagnosis; proxy for the label |
| Endocrinology referrals | **Not represented** | No logical concept defined yet; must be prohibited if a referral concept is added |
| Disease-specific medication patterns (metformin, insulin, GLP-1 RA, SGLT2i) | **Exclude** (via `diabetes_medications`) | Part of the case rule; label-defining |
| Lipid-lowering and antihypertensive drugs | **Allowed if added later** | Not diabetes-specific; would need their own review |

All decisions are method decisions pending clinical reviewer sign-off (V-24).

## Mapping trace

feature → logical concept (`definitions/concepts/`) → realization (`definitions/concept_sets/synthetic/` now;
`omop` empty until verified, V-21c/V-25) → source table (synthetic: `synthetic_observations`; OMOP:
`measurement`, `condition_occurrence`, `drug_exposure`, `visit_occurrence`) → SourceRecord.
