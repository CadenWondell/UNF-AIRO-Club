# ADR-002: Index-visit-bias mitigation and control sampling for the reference kits

- **Status**: accepted (methodological decision; clinical values remain provisional pending V-20)
- **Date**: 2026-10-15
- **Context**: plan § 17 shared M4 questions; `docs/verification/index-visit-bias.md`; V-20.

## Decision

1. Reference kits declare `same_day: exclude_index_day` and `exclude_index_encounter: true`
   (provisional, pending V-20) and `washout: P0D` unless a kit review finds a reason otherwise.
2. Reference kits use `control_sampling.strategy: matched` with
   `match_on: [visit_type, calendar_year]` and a provisional `controls_per_case` (pending V-20).
   Matching uses the existing `matched` strategy; no new sampling mechanism is required.
3. A reusable **index-visit-bias check** is added: an optional kit block
   ```yaml
   visit_bias_check:
     utilization_features: [outpatient_visits, ...]   # registry keys treated as utilization
     max_utilization_auroc: 0.70                      # method decision; reported, not a clinical threshold
   ```
   `leakage/visit_bias.py` fits a utilization-only logistic regression on the training partition and
   reports its validation AUROC against the bound. This is a generic extension point (no kit code).
4. Existing RuleExpr predicates suffice; no new predicate is needed.

## Consequences

- contracts/kit-definition.md and data-model.md gain the optional `visit_bias_check` block.
- Matching can leave some cases without controls; the count of unmatched cases is recorded.
- Sampled development prevalence differs from population prevalence (documented per kit).

## Consistency review (T123)

A manual cross-artifact review of spec.md, plan.md, data-model.md, and contracts/ found no
contradiction: the `matched` strategy and `match_on` attributes already exist in data-model § 2;
the new optional block only adds a reporting check (no CRITICAL/HIGH inconsistency).
`/speckit-analyze` was not run as a separate command.
