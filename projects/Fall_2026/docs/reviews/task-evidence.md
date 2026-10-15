# Task evidence log (Milestones 1–4)

One line per completed task: artifact · check · result. Blocked/deferred tasks are listed with
their blockers.

## Phase 1 — Setup (M1)

| Task | Artifact | Check | Result |
|---|---|---|---|
| T001 | `src/clinical_ml_kits/**`, `definitions/`, `kits/`, `synthetic/`, `tests/`, `docs/` | `find src -type d` | PASS |
| T002 | `pyproject.toml` | clean py3.10 venv: `uv pip install .`; `import clinical_ml_kits` without nbformat | PASS |
| T003 | `uv.lock`, `docs/dependencies.md` | `uv sync --all-extras` | PASS |
| T004 | ruff + mypy config | `uv run ruff check .`; `uv run mypy` | PASS |
| T005 | pytest config, `tests/conftest.py` | `uv run pytest` collected 0 items (pytest's standard "no tests" exit code is 5, not 0 — accepted; superseded once tests exist); `-m workbench` deselected by default | PASS (note) |
| T006 | `.pre-commit-config.yaml` (runs from repository root) | `pre-commit run -c projects/Fall_2026/.pre-commit-config.yaml --all-files` | PASS |
| T007–T014 | `docs/verification/V-01…V-13` | sources recorded; statuses: V-03, V-13 verified; V-01/02/04 unconfirmed; V-10/11/12 unresolved (manual) | DONE (with recorded blockers) |
| T015 | `docs/verification/README.md`; research.md/plan.md updated | manual cross-artifact consistency review (no contradiction with the architecture; `/speckit-analyze` not run as a separate command) | PASS (note) |
| T016 | `docs/conventions.md`, `docs/templates/kit_docs/*` | 7 files; README lists 12 FR-156 questions | PASS |
| T017 | `kits/catalog.yaml` | 25 entries, 3 `reference: true` | PASS |
