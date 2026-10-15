# Clinical background — Type 2 Diabetes

## Why the problem matters
Type 2 diabetes is common and often unrecognized for years; records that are consistent with the
phenotype but lack a diagnosis are a meaningful data-quality and care-gap question for research.

## The phenotype in plain language
A person "meets the phenotype" when their record shows diabetes evidence in combination — repeated
diagnoses, a diagnosis plus treatment, or a diagnosis or treatment plus an abnormal HbA1c — and no
evidence of type 1 or another specific diabetes type. **All thresholds are provisional** pending
review of the ADA Standards of Care and the eMERGE algorithm.

## Why this is phenotype inference, not threshold reproduction
The model never sees HbA1c, glucose, diabetes diagnoses, or diabetes medications — not even earlier
values (FR-134). It must infer the current state from other information (body size, blood pressure,
lipids, liver and renal panels, utilization), which is a genuine learning problem rather than
re-deriving the label's own rule.

## Educational objective
Practice leakage-safe phenotype inference: understand label construction, excluded features,
index-visit bias, sampled prevalence, calibration, and honest evaluation.
