# M4 quickstart run (T174) — 2026-10-15

Commands from `specs/001-clinical-ml-kit-framework/quickstart.md`, run from `projects/Fall_2026/` on
macOS (Python 3.12.13, scikit-learn 1.9.1, pandas 3.0.6) unless noted.

## § 1 Maintainer setup and checks

| Step | Command | Result |
|---|---|---|
| Locked install | `uv sync --all-extras --locked` | PASS |
| Pre-commit | `pre-commit run -c projects/Fall_2026/.pre-commit-config.yaml` (from repo root) | PASS (hooks: ruff, ruff-format, nbstripout, data guard) |
| Tests | `uv run pytest` | PASS — 476 passed |
| Validate all | `uv run ckit validate --all` | PASS — 3 kits `requires_verification` (T2D 12, CKD 19, HTN 19 provisional values; `dataset.version` UNVERIFIED), catalog 25 entries, no provenance errors |
| Synthetic level | `ckit validate kits/all_of_us/<kit> --level synthetic` | PASS for all three |
| Workbench level | `--level workbench` | FAIL as expected for all three, listing every provisional item and every missing `omop` realization |
| Approval level | `--level approval` | FAIL as expected for all three (`approved` refused) |
| Notebook drift | `uv run ckit notebooks --check` | PASS |
| Verification logs | `uv run ckit docs --check` | PASS |

## § 2 Leakage protections

| Step | Command | Result |
|---|---|---|
| Leakage suite | `uv run pytest tests/leakage` | PASS — 41 passed (patient split, grouped CV, test guard, preprocessing isolation, named leakage errors, index-visit bias) |
| Golden values | `tests/unit/features/test_matrix_builder.py`, `test_cutoff_view.py` | PASS — creatinine golden values reproduced by both entry points (include: 1.2/1.0/0.2; exclude_index_day: 1.0/0.9/0.1; 1.5 never visible) |

## § 3 Student flow in synthetic mode

| Kit | Command | Result | Time |
|---|---|---|---|
| T2D | `uv run pytest --nbmake kits/` | PASS (no edits) | 14.5 s |
| CKD | same | PASS | 13.5 s |
| HTN | same | PASS | 10.6 s |
| Setup check | same | PASS | — |

Total with kit test suites: 47 passed in 92 s. Each notebook shows the visible scikit-learn baseline
`Pipeline`, validation metrics, grouped `GridSearchCV`, grouped calibration, explainability, one
logged final evaluation, a valid envelope, and a demo-model save (synthetic only); provisional values
carry the "PROVISIONAL — synthetic-only" banner; section structure is identical across kits (SC-013).

## Colab

| Check | Result |
|---|---|
| Colab-pinned stack (Python 3.13.15, scikit-learn 1.6.1, pandas 2.2.3, numpy 2.1.3; V-13 versions) — local venv and CI job `colab-stack` | PASS — all three kit notebooks and `00_setup_check` execute |
| **Manual Colab smoke run** | **NOT RUN (manual action)**: requires opening each `kit.ipynb` in Google Colab. The notebooks install the pinned tag `v0.1.0`, which has not been pushed yet; a maintainer must push the tag first, then run all cells in a fresh Colab runtime and record the Colab version here |

Remediation tasks: push the `v0.1.0` release tag; perform the manual Colab runs (blocks only the
"manual Colab smoke run" sub-step; synthetic execution is otherwise verified).
