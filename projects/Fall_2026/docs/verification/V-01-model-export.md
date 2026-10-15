# V-01 — Downloading or exporting models trained on All of Us participant-level data

| Field | Value |
|---|---|
| Status | **UNCONFIRMED** (no official text found that addresses trained models specifically) |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (automated source search) |
| Manual action required | Submit an All of Us support ticket (support.researchallofus.org → "Submit a request") asking whether model artifacts trained on registered/controlled tier data may leave the Researcher Workbench. Record the ticket number and answer here. |

## Sources consulted

| Source | Organization | URL | Version/date | Tier |
|---|---|---|---|---|
| Data and Statistics Dissemination Policy (PDF) | All of Us Research Program | https://www.researchallofus.org/wp-content/themes/research-hub-wordpress-theme/media/2020/05/AoU_Policy_Data_and_Statistics_Dissemination.pdf | dated 4/27/2020 | 1 |
| Data Access Framework (support article; HTTP 403 to automated fetch, content summarized by search index only) | All of Us Research Program | https://support.researchallofus.org/hc/en-us/articles/22346942074132-Data-Access-Framework | accessed 2026-10-15 | 1 |
| Frequently Asked Questions | All of Us Research Program | https://www.researchallofus.org/frequently-asked-questions/ | accessed 2026-10-15 | 1 |

## Findings (source evidence)

- The dissemination policy restates the Data User Code of Conduct (DUCC): data users will "NOT take
  screenshots or attempt in any way to copy, download, or otherwise remove any participant-level
  data from the All of Us Researcher Workbench" and will "NOT publish or otherwise distribute any
  participant-level data". It also states the program permits "analysis of data only within its
  secure, cloud-based platform".
- No retrieved official text addresses whether a **trained model** (weights, fitted estimators)
  counts as participant-level data or may be egressed.

## Interpretation (not source evidence)

A fitted model can memorize or encode participant-level information (e.g., KNN stores training
rows; tree leaves can encode small groups). Treating trained research models as non-exportable is
the conservative reading and matches spec FR-095–FR-099.

## Decision

No change to the design. The architecture already assumes research models never leave the
Workbench: `DataEnvironmentPolicy(all_of_us_workbench).portable_artifacts = False` and
`save_model(portable=True)` raises `PolicyViolation` there.

## Remaining uncertainty

Official confirmation of the model-export rule (support ticket pending).

## Affected sections

spec FR-095–FR-099 (unchanged); plan § 21; contracts/dataset-adapter.md (DataEnvironmentPolicy, unchanged).
