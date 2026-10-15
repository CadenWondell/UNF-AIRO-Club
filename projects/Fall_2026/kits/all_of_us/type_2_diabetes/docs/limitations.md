# Limitations — Type 2 Diabetes

## Sampled development prevalence vs population prevalence
Controls are sampled 2 per case (matched), so the outcome rate in the data is the **sampled
development prevalence**, not a population prevalence. Probabilities are relative to that sample and
are not population disease probabilities or clinical risk scores.

## Index-visit bias (residual)
Matching on visit type and calendar year and excluding the index day/encounter reduce, but do not
remove, differences in why case and control visits happened. The utilization-only bias check
reports residual signal.

## Provisional and unverified items
Every clinical threshold, temporal-policy value, and sampling ratio is provisional (V-20, V-21,
V-24, V-25); `omop` concept sets are empty. The kit stays `requires_verification` and cannot run in
the Workbench until these are verified.

## Data and generalization limits
Synthetic data is artificial and not clinically realistic. Real EHR data has heterogeneous coding,
units, and missingness; performance on synthetic data says nothing about real performance.
