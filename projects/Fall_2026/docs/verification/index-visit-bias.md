# Index-visit bias and control sampling (T122)

## Mechanism

Cases are indexed at the date the phenotype is first established, which is usually a diagnostic
encounter with dense testing (confirmatory labs, panels ordered together, follow-up visits). Controls
are indexed at an eligible visit chosen by the framework. If control visits are ordinary visits, a
model can separate cases from controls by **visit context** — how many labs were drawn, how many
visits occurred recently, what kind of visit the index was — instead of by patient physiology. This
inflates performance without clinical meaning (constitution VI-C/D; Albu 2025; Kapoor 2023).

## Mitigations evaluated (plan § 17)

| Mitigation | Effect | Decision |
|---|---|---|
| Exclude index day and index encounter (V-20 options B + C) | Removes the diagnostic encounter's own tests | **Adopt** (provisional per kit) |
| Match control index visits on visit type and calendar year (`control_sampling.strategy: matched`, `match_on: [visit_type, calendar_year]`) | Control index visits look like case index visits in setting and era | **Adopt** as the shared default for the reference kits |
| Additionally match on sex and 10-year age band | Removes demographic imbalance created by sampling | Optional per kit (keeps age/sex usable as predictors when not matched) — not adopted by default |
| Limit utilization-density features (visit counts, measurement counts) near the index | Prevents learning testing intensity | **Adopt**: utilization features use a lookback window that ends at the effective cutoff (index day excluded), and measurement `count` derivations are reviewed per kit (V-24) |
| `random_ratio` sampling | Simple; controls indexed at random eligible visits | Not adopted for reference kits (does not address visit context) |
| `all_eligible` | Uses every eligible control; sampled prevalence closest to the eligible-population prevalence | Not adopted (still one random visit per control; no context matching) |

## Control sampling and prevalence

Any strategy other than `all_eligible` fixes the case:control ratio, so the **sampled development
prevalence** (recorded in every SplitManifest and envelope `probability_basis: development_sample`)
differs from the population prevalence. Calibration and threshold metrics (precision, F1, PPV) are
therefore relative to the sample. Notebooks (section 10) and each kit's `limitations.md` state this;
converting to population probabilities would need a documented recalibration method, out of scope
for M1–4.

## Measurable checks (implemented in `leakage/visit_bias.py`, T124–T125)

1. **Utilization-only model**: fit a logistic regression on utilization features only (visit counts
   by type and per-measurement counts) on the training partition and report its validation AUROC.
   If it exceeds the kit's configured bound (`visit_bias_check.max_utilization_auroc`, a method
   decision), the check reports **index-visit bias** (warning in synthetic mode; recorded for
   review).
2. **Match quality**: for `matched` sampling, every control's index visit equals its case's index
   visit on each `match_on` attribute (tested).

## Residual limitations

- Matching on visit type/year does not remove differences in *why* a visit happened.
- Excluding the index day removes legitimate same-day information.
- The bound on utilization-only AUROC is a method decision, not a validated threshold.
- Synthetic populations only exercise these mechanisms; real-data behavior must be assessed inside
  the Workbench (FR-081 evidence).
