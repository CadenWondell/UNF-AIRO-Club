# Limitations — Hypertension

## Sampled development prevalence vs population prevalence
Matched 2:1 control sampling sets the sampled development prevalence; probabilities are relative to
that sample and are not population disease probabilities or clinical risk scores.

## Index-visit bias (residual)
Controls must accumulate two normal readings before they are eligible, so their index visits tend to
come later in their records with more prior visits, while cases are indexed at the first qualifying
reading. On the synthetic population the utilization-only check reports a validation AUROC of about
0.69 (bound 0.70) — prior-visit counts carry index-selection information, not physiology. Students
should test models with and without `outpatient_visits__count`.

## Provisional and unverified items
All thresholds, reading counts, exclusions, temporal policy, and sampling ratio are provisional
(V-20, V-23, V-24, V-25); `omop` concept sets are empty.

## Data and generalization limits
Office BP readings are noisy and measurement protocols vary. Synthetic data is artificial and not
clinically realistic.
