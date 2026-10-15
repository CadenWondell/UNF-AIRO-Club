# V-20 — Same-day, washout, index-encounter, and diagnostic-workup exclusion (shared methodology)

| Field | Value |
|---|---|
| Status | **OPTIONS DOCUMENTED; no per-kit value verified.** Per-kit choices are made in T133/T148/T163 as **provisional** values pending reviewer verification. |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (literature search; abstracts and metadata via Europe PMC, primary guideline PDFs where retrievable) |

## Sources (tiers 4–6)

| Source | Tier | What it supports |
|---|---|---|
| `albu_2025_ehr_extraction` — Albu et al., JMIR 2025, doi:10.2196/73987 | 5 | Label leakage arises when the prediction time is too close to the event: features then "detect rather than predict" the outcome. Supports excluding observations at/near the index (diagnostic workup). |
| `kapoor_2023_leakage` — Kapoor & Narayanan, Patterns 2023, doi:10.1016/j.patter.2023.100804 | 6 | Taxonomy of leakage including temporal leakage and features that are proxies for the outcome. |
| `tripod_ai_2024` — Collins et al., BMJ 2024, doi:10.1136/bmj-2023-078378 | 5 | Reporting must state when predictors were measured relative to the outcome/index; supports declaring the policy explicitly. |
| `kdigo_ckd_2024` | 4 | CKD requires abnormalities present ≥ 3 months, so the CKD index date is a chronicity date (affects same-day reasoning for CKD). |
| Search result (not used as a source): a 2026 All of Us study (PMC13256376) used predictors strictly before index and a 30-day gap before counting outcomes; this concerns future-outcome prediction, not current-state inference, so it is noted only as context. | — | — |

No tier 1–4 source prescribes same-day or washout rules for **current-state phenotype inference**;
these are methodological decisions (FR-137), hence tiers 5–6 (P-9 justification).

## Candidate options (per kit decision later)

| Option | Mechanism (framework field) | Evidence / rationale | Cost |
|---|---|---|---|
| A. Include the index day | `same_day: include` | Simplest; index-day non-defining labs are available "at" index | Highest workup leakage: tests ordered with the diagnostic test (e.g., metabolic panel with HbA1c) and their presence reveal the label (Albu 2025) |
| B. Exclude the index day | `same_day: exclude_index_day` | Removes same-day diagnostic workup; date-only rows count as same day | Loses legitimate same-day information |
| C. Exclude the index encounter | `exclude_index_encounter: true` | Removes the diagnosing encounter even if it spans days | Requires visit linkage (V-11) |
| D. Washout before index | `washout: PnD` | Removes the pre-diagnostic workup run-up (days–weeks of testing before the diagnosis) | Loses recent information; sparser features |
| E. Windowed exclusion of workup concepts | `windowed_exclusions` on specific concepts/domains | Targets known workup tests (e.g., kidney imaging/procedures around CKD index) | Needs a reviewed list per kit |

## Recommendation for provisional synthetic values (to be verified)

Combine **B + C** for all three kits (exclude index day and index encounter), with **washout 0 days**
initially and kit-specific windowed exclusions only where a workup concept is identified in V-24
review. These are provisional (pending V-20) and must be reviewed per kit; the index-visit-bias
check (ADR-002) measures residual leakage through utilization features.

## Affected sections

contracts/kit-definition.md (temporal_policy), plan § 17 shared questions, T133, T148, T163.
