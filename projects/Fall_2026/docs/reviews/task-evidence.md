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

## Phase 2 — Foundational (M1), part 2

| Task | Artifact | Check | Result |
|---|---|---|---|
| T042 | `docs/decisions/ADR-001-notebook-templating.md` | status accepted | PASS |
| T043–T044 | `notebooks/render.py` | `tests/unit/notebooks/test_templating.py` | PASS |
| T045–T046 | `notebooks/builder.py`, `skeletons/_common/`, `kits/00_setup_check.ipynb` | `tests/unit/notebooks/test_builder.py`; nbmake executes `00_setup_check.ipynb` | PASS |
| T047–T048 | `notebooks/checks.py`; 21 negative + 1 positive fixture | `tests/notebooks/test_content_rules.py` (every negative caught by its rule) | PASS |
| T049 | `tests/notebooks/test_drift.py` | passes vacuously until kit notebooks exist | PASS |
| T050 | `ckit notebooks [--kit] [--check]` | implemented; `--check` on a hand-edited kit notebook is verified once the toy notebook exists (T119) | IN PROGRESS |
| T051–T052 | `provenance/report.py`, `ckit docs [--kit] [--check]` | `tests/unit/docs/test_verification_report.py` (hand edit detected; P-11 status fields rejected) | PASS |
| T053–T054 | `provenance/kitdocs.py`, approval-level README check | `tests/unit/docs/test_kitdocs_answers.py` (missing answer and broken link detected). Note: the README helper was first written with T026 because the approval level needed it; T053's tests were then written and run against broken fixtures. | PASS (note) |
| T055–T057 | `adapters/synthetic_clinical/golden.py`, `synthetic/golden/*.yaml`, README | `tests/unit/synthetic/test_golden_loader.py`; all four fixtures load with the provenance header | PASS |
| T058 | `/.github/workflows/clinical-ml-kits.yml` (3.10 + 3.13) | local: full suite passes on Python 3.12 and 3.10; GitHub run recorded below | see CI |
| T058 | CI workflow | GitHub Actions push run 38776411847 green on Python 3.10 and 3.13 (https://github.com/CadenWondell/UNF-AIRO-Club/actions/runs/38776411847); first run 38776054986 failed at notebook drift (fixture kit without Template A) and was fixed with `generate_notebook: false` | PASS |

## Phase 3 — M2, part 1

| Task | Artifact | Check | Result |
|---|---|---|---|
| T059–T060 | `features/concept_sets.py` (domain-consistency rule added), `definitions/concepts/*` (39 FR-031 logical concepts, `requires_verification`), `definitions/concept_sets/synthetic/*` (SYN- codes), READMEs; no OMOP IDs | `tests/unit/features/test_concept_sets.py` (domain test failed first) | PASS |
| T061–T062 | `data/adapter.py`, `data/schemas.py`, `data/registry.py` | `tests/contract/test_adapter_contract.py` (failed only for lack of an adapter) | PASS |
| T063–T064 | `adapters/synthetic_clinical/adapter.py` (golden backend; unit rejection; namespace isolation) | `tests/unit/adapters/test_synthetic_adapter.py`, contract suite `[synthetic_clinical]` | PASS |
| T065–T066 | `adapters/synthetic_clinical/generator.py`, `params.py` (header + planted-relationship enforcement), `synthetic/generator_params/{default.yaml,README.md}`, full fixture params | `tests/unit/adapters/test_generator.py` (failed first on branch wip/m2-generator; determinism, params-only I/O, header, planted listing, cases/controls, missingness, density, size) | PASS |
| T067–T068 | `adapters/all_of_us/adapter.py` (fails closed: no verified V-10 markers → `EnvironmentNotPermitted`, even with legacy env vars; data methods raise `PendingVerification("V-10/V-11")`; no SQL/clients) | `tests/unit/adapters/test_aou_boundary.py` | PASS |
| T069 | `tests/repo/test_import_boundaries.py` | passes; planted bad imports caught | PASS |
| T070–T071 | `temporal/policy.py`, `temporal/cutoff.py` (date-precision index; rules 1–4) | `tests/unit/temporal/test_policy.py` (8-policy same-day golden matrix) | PASS |
| T072–T073 | `features/timeline.py` (`PatientTimeline`, immutable `CutoffView`, `Obs`, `Missing`) | `tests/unit/features/test_cutoff_view.py` (creatinine golden: include 1.2/1.0/0.2, exclude 1.0/0.9/0.1, 1.5 unreachable). One test expectation of mine was wrong (P200D window covers 2 visits) and was corrected with the arithmetic in a comment | PASS |
| T074–T075 | `features/derivations.py` (shared, groupby-vectorized) | `tests/unit/features/test_derivations.py` | PASS |
| T076–T077 | `features/matrix.py` (`FeatureMatrixBuilder`, lineage) | `tests/unit/features/test_matrix_builder.py` (equals the patient view for every golden patient × derivation × same-day mode; lineage before cutoff) | PASS |
| T078–T079 | `features/registry.py` (`resolve`, `flag_out_of_range`), `definitions/features/registry.yaml` (39 features; units provisional V-25; ranges UNVERIFIED; no OMOP IDs) | `tests/unit/features/test_registry.py` | PASS |
| T080–T081 | `provenance/trace.py` (written with P-8 in T032) | `tests/unit/provenance/test_traceability.py` (every registry feature traces; broken links named) | PASS (impl preceded this test) |
