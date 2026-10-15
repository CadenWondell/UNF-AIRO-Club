# V-13 — Google Colab runtime versions

| Field | Value |
|---|---|
| Status | **VERIFIED** (official Colab backend package list) |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (automated source verification) |

## Sources

| Source | Organization | URL | Version/date | Tier |
|---|---|---|---|---|
| googlecolab/backend-info `pip-freeze.txt` and `os-info.txt` | Google Colab | https://github.com/googlecolab/backend-info | commit `92a2364a31cd`, 2026-10-02 | 1 (official runtime manifest) |
| Colab runtime version FAQ | Google | https://research.google.com/colaboratory/runtime-version-faq.html | snapshots 2026.01–2026.07 | 1 |

## Findings (current default CPU runtime per backend-info, 2026-10-02)

| Item | Version |
|---|---|
| OS | Ubuntu 24.04.5 LTS |
| Python | 3.13.16 |
| numpy | 2.1.3 |
| pandas | 2.2.3 |
| scikit-learn | 1.6.1 |
| scipy | 1.16.3 |
| pydantic | 2.13.5 |
| matplotlib | 3.10.0 |
| PyYAML | 6.0.3 |
| joblib | 1.6.0 |

The runtime FAQ lists earlier pinned snapshots with Python 3.12.x (2026.01–2026.07); the backend
manifest shows the current default has moved to Python 3.13 (backend-info notes the list reflects the
most recent submitted change, not necessarily production at every moment).

## Decision

- CI Python matrix: **3.10** (declared floor) and **3.13** (current Colab default).
- All package pins in `pyproject.toml` admit the Colab versions above, so `%pip install` does not
  force upgrades of preinstalled numpy/pandas/scikit-learn.
- V-14 is tested empirically against scikit-learn **1.6.1** (Colab) as well as the maintainer lock.

## Affected sections

research R-01 (Colab default is now 3.13, not 3.12); T058, T088.
