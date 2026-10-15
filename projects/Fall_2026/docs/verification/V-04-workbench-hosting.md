# V-04 — Can the Workbench host, serve, or execute models for external consumers?

| Field | Value |
|---|---|
| Status | **UNCONFIRMED** |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (automated source search) |
| Manual action required | Include this question in the V-01 support ticket. |

## Sources consulted

| Source | Organization | URL | Version/date | Tier |
|---|---|---|---|---|
| Release of Researcher Workbench 2.0 (search-index summary; direct fetch HTTP 403) | All of Us Research Program | https://support.researchallofus.org/hc/en-us/articles/46436081497748-Release-of-Researcher-Workbench-2-0-for-CDRv8-Controlled-Tier | 2026 | 1 |
| Verily Workbench release notes | Verily | https://support.workbench.verily.com/docs/release_notes/ | accessed 2026-10-15 | 1 (platform vendor docs) |

## Findings

- The Researcher Workbench is now "Researcher Workbench 2.0", powered by Verily Workbench; the
  legacy workbench is retired (search-index summary of the official support article).
- Verily release notes describe JupyterLab apps, batch VMs (with a network policy limiting internet
  access for batch VMs), and Dataproc; no model-serving capability for external consumers is
  described.

## Decision

No design change. The framework never relies on Workbench hosting (FR-099). Dashboards use demo
models trained on synthetic data only.

## Remaining uncertainty

Whether any sanctioned serving capability exists.

## Affected sections

spec FR-099; plan § 21. Nothing in M1–4.
