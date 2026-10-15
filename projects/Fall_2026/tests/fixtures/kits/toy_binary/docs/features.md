# Features — toy binary kit
## Included features
fx_age, fx_bmi, fx_creatinine, fx_sodium, fx_comorbidity (count), fx_outpatient_visits (count, last 365 days).
## Excluded features
fx_dx and fx_marker: label-defining.
## Mapping trace
feature → `fx_*` logical concept → synthetic realization → `synthetic_observations` → fixture_methods.
