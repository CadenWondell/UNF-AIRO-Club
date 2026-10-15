# V-12 — Workbench Jupyter runtime versions

| Field | Value |
|---|---|
| Status | **UNRESOLVED** (requires Workbench access) |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (automated source search) |
| Manual action required | In a Researcher Workbench 2.0 JupyterLab app run `python -V` and `pip list` (record numpy, pandas, scikit-learn, pydantic, matplotlib, PyYAML, google-cloud-bigquery) and test `pip install` from GitHub. Record the date. |

## Sources consulted

| Source | Organization | URL | Version/date | Tier |
|---|---|---|---|---|
| Verily Workbench release notes | Verily | https://support.workbench.verily.com/docs/release_notes/ | accessed 2026-10-15 | 1 (vendor) |

## Findings

Release notes describe JupyterLab apps on a custom GCE configuration (replacing Vertex AI
notebooks) and a network policy that limits internet access **for batch VMs**; they do not list
Python or package versions or JupyterLab app internet access.

## Decision

- Keep `requires-python >= 3.10` and wide compatible-range dependency pins (numpy ≥1.24, pandas ≥2.0,
  scikit-learn ≥1.3, pydantic ≥2.5) so the package can coexist with an unknown preinstalled stack.
- The framework's code is tested on the oldest supported Python (3.10) and the Colab Python (3.13);
  scikit-learn behavior that matters (grouped calibration) is handled version-independently (V-14).

## Affected sections

T058 (CI matrix uses V-13 + the 3.10 floor), T088 (V-14 cannot record the Workbench version).
