# V-10 — Workbench data-access mechanism and CDR version naming

| Field | Value |
|---|---|
| Status | **UNRESOLVED** (platform changed; current Python access pattern not confirmed from official docs) |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (automated source search) |
| Manual action required | Inside a Researcher Workbench 2.0 JupyterLab app, record: (1) which environment variables are set in the **kernel** (`sorted(os.environ)`; do not record values that identify the workspace beyond what is needed); (2) the documented way to obtain the CDR BigQuery dataset reference; (3) the BigQuery client library and version (`google-cloud-bigquery`); (4) authentication (default credentials?); (5) the CDR version name. Cite the official support article used. |

## Sources consulted

| Source | Organization | URL | Version/date | Tier |
|---|---|---|---|---|
| Release of Researcher Workbench 2.0 for CDRv8 Controlled Tier (search-index summary; direct fetch HTTP 403) | All of Us Research Program | https://support.researchallofus.org/hc/en-us/articles/46436081497748 | 2026 | 1 |
| Researcher Workbench 2.0 Glossary of Terms and Comparison Guide (search-index summary) | All of Us Research Program | https://support.researchallofus.org/hc/en-us/articles/44371414196116 | 2026 | 1 |
| What to expect during the Researcher Workbench Migration (search-index summary) | All of Us Research Program | https://support.researchallofus.org/hc/en-us/articles/39985865987732 | 2025 | 1 |
| Work with workspace context environment variables | Verily | https://support.workbench.verily.com/docs/guides/cli/workspace_context/ | accessed 2026-10-15 | 1 (platform vendor) |
| aoutools `_workbench` module source (third party) | aoutools project | https://aoutools.readthedocs.io/en/dev/_modules/aoutools/_workbench.html | dev docs, accessed 2026-10-15 | 6 |
| allofus R package README (third party) | CRAN mirror | https://mirror.niser.ac.in/cran/web/packages/allofus/readme/README.html | accessed 2026-10-15 | 6 |

## Findings

- The legacy Researcher Workbench is retired; **Researcher Workbench 2.0** runs on Verily Workbench
  (JupyterLab apps). CDR v8 Controlled Tier is available there; older CDR versions (v5, v6) are not.
- Verily documents a workspace context with `GOOGLE_CLOUD_PROJECT`, `GOOGLE_SERVICE_ACCOUNT_EMAIL`,
  and `WORKBENCH_<resource>` variables for workspace resources (vendor docs).
- Third-party tooling (tier 6) reports that `WORKSPACE_CDR`, `WORKSPACE_BUCKET`, and `GOOGLE_PROJECT`
  are **no longer** set as environment variables on Workbench 2.0 and are resolved through the `wb`
  CLI instead. This is not official and was not confirmed.

## Decision

- The All of Us adapter's environment guard **fails closed**: until this record lists verified
  Workbench markers, the adapter refuses to initialize anywhere (`EnvironmentNotPermitted`) and all
  data methods raise `PendingVerification("V-10/V-11")`. No marker is guessed.
- The `[aou]` extra stays empty. T126–T127 (SQL builder) remain blocked.

## Remaining uncertainty

The entire Python access pattern for Workbench 2.0 notebooks, and CDR naming.

## Affected sections

research R-17 (the legacy `WORKSPACE_CDR` pattern may be obsolete); contracts/dataset-adapter.md
(environment markers pending); T068 (guard fails closed), T126–T128, T142, T157, T172.
