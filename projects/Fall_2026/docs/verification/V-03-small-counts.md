# V-03 — Small-count dissemination rule

| Field | Value |
|---|---|
| Status | **VERIFIED** (official policy text, tier 1) |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (automated source verification against the official policy PDF and the official policy summary page). Maintainer confirmation is recommended at the next review. |
| Structured record | `definitions/sources/aou_dissemination_policy.yaml` (the code reads parameters only from this record) |

## Sources

| Source | Organization | URL | Version/date | Tier |
|---|---|---|---|---|
| All of Us Research Program Data and Statistics Dissemination Policy (full policy PDF) | All of Us Research Program | https://www.researchallofus.org/wp-content/themes/research-hub-wordpress-theme/media/2020/05/AoU_Policy_Data_and_Statistics_Dissemination.pdf | Policy dated 4/27/2020; retrieved 2026-10-15 | 1 |
| Data and Statistics Dissemination Policy (official summary page) | All of Us Research Program | https://www.researchallofus.org/?p=4698 | Page © 2026; retrieved 2026-10-15; summary text matches the PDF policy statement | 1 |
| How to comply with the All of Us Data and Statistics Dissemination Policy (support article; automated fetch HTTP 403, content seen only via search index) | All of Us Research Program | https://support.researchallofus.org/hc/en-us/articles/360043016291 | accessed 2026-10-15 | 1 |

## Source evidence (verbatim, policy PDF "POLICY STATEMENT")

> 1. No participant count of 1 to 20 can be published or distributed directly (a count of 0 is
>    permitted); and
> 2. No data or statistics can be reported that allow a participant count of 1 to 20 to be derived
>    from other reported cells or information, including in text, tables, or figures. This includes
>    the use of percentages or other mathematical formulas that in combination would allow an
>    individual to deduce a participant count of less than 20.

> This policy permits data users who wish to report data or aggregate statistics that correspond to
> fewer than 20 participants to obscure these values using scientifically accepted strategies,
> including collapsing data across cells, coarsening data, or cell suppression.

Background section: data users will "NOT publish or otherwise distribute any participant-level data"
and "NOT publish or otherwise distribute any data or aggregate statistics corresponding to fewer than
20 participants unless expressly permitted"; the program permits "analysis of data only within its
secure, cloud-based platform".

## Answers

**(a) Exact threshold.** Counts **1 through 20 inclusive** may not be published or distributed;
**0 is permitted**. (The background text says "fewer than 20" while the policy statement says
"1 to 20"; the framework applies the stricter, explicit policy-statement range 1–20.)

**(b) Scope.** Any data or aggregate statistic that is published or distributed: participant counts,
and any data/statistics from which a count of 1–20 can be **derived**, in text, tables, or figures,
including percentages or other formulas that in combination reveal such a count.

**(c) Inside vs leaving the Workbench.** The policy governs publication/distribution of results.
Analysis and in-session display **inside** the Workbench are not restricted by this policy (the
program permits analysis only within its platform). Anything leaving the Workbench is restricted.

**(d) Effect on outputs that leave the Workbench.**

| Output | Rule applied by the framework (`completion/suppression.py`) |
|---|---|
| Confusion-matrix cells | Each cell with count 1–20 is suppressed (`"<=20"`); if exactly one cell in the matrix is suppressed, a complementary cell is also suppressed so it cannot be recovered from reported totals |
| Calibration-bin counts | Bin counts 1–20 suppressed; observed event rates of bins whose count or event count is 1–20 are suppressed |
| Subgroup tables | Same as counts; percentages/rates suppressed when their numerator or denominator is 1–20 |
| Descriptive statistics / cohort descriptions | Counts 1–20 suppressed; derived percentages suppressed as above |
| Derived metrics (AUROC, AUPRC, sensitivity, specificity, precision, F1, Brier, prevalence) | Suppressed when the positives, negatives, or evaluated rows they are computed from number 1–20 (the metric could, with the reported N, reveal a small count) |
| FR-081 evidence fields | Counts and coverage fractions follow the same rules |

**(e) Public GitHub repository.** Committing to a public repository is publication/distribution, so
every aggregate copied into the repository (README statistics, notebook outputs, generated
figures, CI artifacts, `evidence/fr081.yaml`, `verification.yaml` notes) must satisfy the rules
above. Being aggregate does not by itself make a result publishable. In addition, the
framework's CI never touches All of Us data, so CI artifacts contain synthetic results only.

## Decision

Implement the dissemination filter using parameters from the structured SourceRecord
(`suppress_min: 1`, `suppress_max: 20`, `zero_permitted: true`, `derived_values_restricted: true`).
No threshold literal appears in framework code.

## Remaining uncertainty

- Whether the program has issued newer guidance (e.g., for Researcher Workbench 2.0) that changes the
  rule; the 2026 summary page matches the 2020 policy statement.
- Detailed acceptable-strategy guidance is on the Support Hub (not retrievable by automated fetch).

## Affected sections

plan § 21 and R-15 (threshold now known; architecture unchanged); contracts/dataset-adapter.md
(DataEnvironmentPolicy aggregate rule now sourced); T030, T114, T115, T128.
