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

## Phase 2 — Foundational (M1), part 1

| Task | Artifact | Check | Result |
|---|---|---|---|
| T018–T019 | `core/errors.py`, `core/logging.py` | `tests/unit/core/test_logging.py` (failed on import first) | PASS |
| T020–T021 | `core/seeds.py`, `core/run_manifest.py` | `tests/unit/core/test_run_manifest.py` | PASS |
| T022–T023 | `provenance/models.py` | `tests/unit/provenance/test_models.py` | PASS |
| T024–T026 | `core/values.py`, `core/kit_schema.py`; 23 invalid + 2 valid fixtures in `tests/fixtures/kits/` | `tests/unit/core/test_kit_schema.py` (each invalid fixture fails at its level naming the field; provisional passes schema/synthetic, fails workbench/approval listing items; verified passes all four) | PASS |
| T027–T028 | `prediction/envelope.py` (v1.0.0) | `tests/contract/test_envelope.py` | PASS |
| T029–T030 | `data/policy.py`, `definitions/sources/aou_dissemination_policy.yaml` | `tests/unit/data/test_policy.py` (no numeric small-count literal in policy.py) | PASS |
| T031–T032 | `provenance/checks.py`, `provenance/hashing.py`, `provenance/trace.py`; fixtures `tests/fixtures/provenance/` | `tests/unit/provenance/test_checks.py` (P-1…P-11; P-4 blocks approved) | PASS |
| T033–T034 | `core/schema_export.py`, `docs/schemas/*.schema.json` | `tests/unit/core/test_json_schema.py` (byte-for-byte) | PASS |
| T035–T037 | `core/catalog.py` | `tests/unit/core/test_catalog.py` (repository catalog: 25 candidates, 3 reference) | PASS |
| T038–T039 | `cli.py` (`validate --level`, `--all`, `catalog`, `schemas`, `stamp`) | `tests/unit/test_cli.py` | PASS |
| T040–T041 | `tests/repo/data_guard.py`, pre-commit hook | `tests/repo/test_data_guard.py`; pre-commit hook rejected a planted `docs/persons.csv` | PASS |

Schema notes (additive refinements, recorded in contracts/kit-definition.md § Implementation notes):
`target {code, label}` (required by the envelope), optional `review {reviewer, signed_on}` (approval
sign-off), verified values use the explicit form `{value, provenance}`, durations are restricted to
`PnD`/`PnW`, split salts end with `-s<salt_version>`, and inline phenotypes are accepted for test
fixtures.
