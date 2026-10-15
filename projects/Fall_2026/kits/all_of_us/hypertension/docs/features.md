# Features — Hypertension (`aou_htn_current`)

## Included features

| Feature | Derivations | Why it is allowed |
|---|---|---|
| `age`, `sex_at_birth` | latest | Demographic context |
| `bmi` (latest, mean), `weight` | | Adiposity correlates with hypertension; not phenotype evidence |
| `heart_rate` | latest | Vital sign not used by the phenotype; same-visit values on the index day are excluded |
| `glucose`, `hba1c` | latest | Allowed for this kit (plan § 17.3) |
| `ldl`, `hdl`, `triglycerides` | latest | Lipids |
| `creatinine`, `sodium`, `potassium` | latest | Renal panel and electrolytes; not part of this phenotype |
| `outpatient_visits` | count (last 365 days) | Utilization; monitored by the index-visit-bias check |

## Excluded features

| Item | Reason | Decision source |
|---|---|---|
| `htn_diagnosis`, `systolic_bp`, `diastolic_bp`, `antihypertensive_medications` | label-defining (earlier values too, FR-134) | FR-135, phenotype |
| `pregnancy_hypertension`, `secondary_hypertension` | label-source (exclusions) | phenotype |
| `hypertensive_heart_kidney_disease` | indirect label revealer | V-24 review |
| `home_bp_monitoring` | indirect label revealer | V-24 review |

## Indirect label-revealer review (V-24)

| Category | Decision | Justification against the prediction question |
|---|---|---|
| Hypertensive heart/kidney disease codes | **Exclude** | Coded only when hypertension is recognized |
| Home BP monitoring | **Exclude** | Prescribed for diagnosed or suspected hypertension |
| Antihypertensives used for other indications (beta-blockers for AF, ACE inhibitors/ARBs for heart failure or diabetic kidney disease) | **Exclude all antihypertensives** | Part of the case rule; cannot separate indications reliably from structured data. The case rule never accepts medication alone, so AF patients on beta-blockers are not labeled cases |
| Same-visit heart rate | **Allowed historically; index day excluded** | Heart rate is not phenotype evidence; the same-day rule removes vitals taken with the confirming BP |
| Atrial fibrillation diagnosis | **Not used as a feature** | Context only in the synthetic data |

## Mapping trace

feature → logical concept → realization (synthetic now; `omop` empty until V-23c/V-25) → source table → SourceRecord.
