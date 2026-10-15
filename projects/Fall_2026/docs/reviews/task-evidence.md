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
| T050 | `ckit notebooks [--kit] [--check]` | after T119: `--check` exited 1 on a hand-edited `tests/fixtures/kits/toy_binary/kit.ipynb` (C=9.0) and 0 after regeneration (byte-identical to the committed file) | PASS |
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
| T082–T083 | `cohort/rules.py` (vectorized RuleExpr evaluator) | `tests/unit/cohort/test_rules.py` on `tests/fixtures/golden/cohort_rules.yaml` | PASS |
| T084–T085 | `cohort/labels.py`, `cohort/index.py`, `cohort/sampling.py` | `tests/unit/cohort/test_labels.py` (earliest-date case index; positive-evidence controls; "no evidence" excluded; min history; all_eligible/random_ratio/matched one row per person, reproducible, sampled prevalence; features unchanged by labels) | PASS |
| T086–T087 | `splitting/hash_split.py`, `splitting/manifest.py`, `docs/privacy/split-metadata.md` | `tests/leakage/test_split.py` | PASS |
| T088 | `docs/verification/V-14-grouped-calibration.md`, `docs/verification/scripts/v14_probe.py`, `definitions/sources/v14_grouped_calibration.yaml` | probe on scikit-learn 1.3.2, 1.6.1 (Colab), 1.9.1: no groups without metadata routing; selected pattern = grouped OOF helper; Workbench version unknown (V-12) | DONE |
| T089–T090 | `splitting/groups.py` (masked `OpaqueGroups`, collision check), `splitting/cv.py` (`PatientGroupedKFold`), `evaluation/grouped_calibration.py`, `splitting/datasets.py` | `tests/leakage/test_grouped_cv.py` (synthetic and Workbench-environment KitData; no group crosses folds; GridSearchCV with groups sees only train rows; calibration folds respect groups) | PASS |
| T091–T092 | `splitting/guard.py` (module-private vault, logged, warns on repeat) | `tests/leakage/test_test_guard.py` (my first draft compared positional indices; rewritten to compare person IDs and feature values) | PASS |
| T093–T094 | `leakage/checks.py` (patient, temporal lineage, same-day/index-encounter, target overlap, undeclared label sources, prohibited, preprocessing fit size) | `tests/leakage/test_checks.py` (each planted case raises its named error; justified inclusion passes) | PASS |
| T095–T097 | toy kit `tests/fixtures/kits/toy_binary/` (+ docs), `tests/fixtures/synthetic/generator_params/toy_binary.yaml`, `core/kit.py` (`load_kit`, `Kit.load/patient/describe/cv_splitter/calibrate_grouped/feature_spec`) | `tests/integration/test_load_kit.py` (synthetic level; AoU refused before data access and at workbench level; population not golden; ≥10 positives per partition: train 321, validation 72, test 61; groups present, not in X; one row per person, duplicate rejected; min_features_present logged before split; label concepts excluded; RunManifest populated) | PASS |

**M2 exit**: all M2 tests green (362); the synthetic adapter builds the toy cohort and feature matrix from its generator population; the import-boundary test passes (it caught and blocked a `core → adapters` import during T097); the All of Us adapter holds no queries.

## Phase 4 — M3 (Template A), part 1

| Task | Artifact | Check | Result |
|---|---|---|---|
| T098–T099 | `preprocessing/factory.py` (`make_preprocessor`) | `tests/leakage/test_preprocessing_isolation.py` (train-only statistics; perturbing validation leaves fit unchanged; indicators; no numeric constant fill). Indicator columns are standardized by the plan's scaler, so the test checks the flagged row rather than raw 0/1 | PASS |
| T100–T101 | `evaluation/metrics.py`, `evaluation/threshold.py` | `tests/unit/evaluation/test_metrics.py` (hand-computed AUROC 14/16, AP, confusion, Brier; youden/max_f1 = 0.7) | PASS |
| T102–T103 | `evaluation/calibration.py` | `tests/unit/evaluation/test_calibration.py` (calibrated data: slope≈1, intercept≈0; text says development sample, not a clinical risk score) | PASS |
| T104–T105 | `evaluation/explain.py` | `tests/unit/evaluation/test_explain.py` (contributions sum to logit − intercept) | PASS |
| T106–T107 | `evaluation/plots.py`, `evaluation/compare.py` | `tests/unit/evaluation/test_plots_compare.py` | PASS |
| T108–T109 | `evaluation/final.py`, `Kit.final_evaluation` | `tests/unit/core/test_final_evaluation.py` (logged once, warns on repeat, threshold reused, LR/RF/GB/SVC/KNN accepted, leaky preprocessor rejected — this test exposed a traversal bug in `check_preprocessing_fit` that skipped nested scalers; fixed — non-Pipeline warns) | PASS |
| T110–T111 | `prediction/build.py`, `Kit.to_envelopes` | `tests/unit/prediction/test_to_envelopes.py` | PASS |
| T112–T113 | `completion/record.py`, `save.py`, `portable.py`, `Kit.complete`, `Kit.save_model` | `tests/unit/completion/test_policy_matrix.py` (portable refused in Workbench; checkout writes refused; portable definition has no data/model) | PASS |
| T114–T115 | `completion/suppression.py` (parameters only from the V-03 record) | `tests/unit/completion/test_suppression.py` (1–20 suppressed, 0 allowed, complementary confusion-cell suppression, bins, derived metrics, subgroups; unresolved V-03 blocks) | PASS |
| T116–T117 | `notebooks/skeletons/binary_tabular/skeleton.yaml`, `templates/binary_tabular/notebook.py` | `tests/notebooks/test_binary_tabular_skeleton.py` (13 sections; visible LogisticRegression Pipeline with kit.yaml params rendered literally and tracking edits; RF/HGB/SVC/KNN starters; grouped GridSearchCV; no test access in §§7–11; grouped calibration and prevalence text; provisional banner; content rules) | PASS |
| T118–T119 | `tests/fixtures/kits/toy_binary/kit.ipynb` (generated) | `tests/notebooks/test_toy_notebook_exec.py`: runs end to end with no edits in ~10 s (<300 s); instrumentation confirms no group crosses GridSearchCV folds, final_evaluation ran once, data from `toy_binary.yaml` (seed 20261015, 1500 persons); `test_drift.py[toy_binary]` | PASS |
| T120 | `tests/integration/test_reproducibility.py` | identical manifests, features, coefficients, threshold, metrics, RF probabilities across two runs | PASS |

Compatibility checks at M3 exit: full suite on Python 3.10 (pandas 2.3, scikit-learn 1.7) and on the Colab stack (Python 3.13, scikit-learn 1.6.1, pandas 2.2.3, numpy 2.1.3): 422 passed each, after fixing `None` handling for categorical columns on older pandas. scikit-learn capped `<1.10` because `penalty` (rendered literally) is removed in 1.10. CI gained a `colab-stack` job.

**M3 exit**: the toy kit notebook completes in synthetic mode in about 10 seconds with visible scikit-learn baseline code; all template tests green.

## Phase 5 — M4, shared methodology

| Task | Artifact | Check | Result |
|---|---|---|---|
| T121 | `docs/verification/V-20-temporal-policies.md`; SourceRecords `albu_2025_ehr_extraction`, `kapoor_2023_leakage`, `tripod_ai_2024` | options A–E with citations; no per-kit decision | DONE |
| T122 | `docs/verification/index-visit-bias.md` | mechanism, mitigations, sampling/prevalence, measurable checks, residual limitations | DONE |
| T123 | `docs/decisions/ADR-002-index-visit-bias.md` (accepted); contracts/kit-definition.md and data-model.md gain optional `visit_bias_check` | manual consistency review (no CRITICAL/HIGH; `/speckit-analyze` not run separately) | DONE |
| T124–T125 | `leakage/visit_bias.py`, `KitDefinition.visit_bias_check`, `Kit.load` integration; fixture population `tests/fixtures/synthetic/generator_params/visit_bias.yaml` (test-scoped instead of `synthetic/generator_params/` because it uses fixture concepts) | `tests/leakage/test_index_visit_bias.py` (utilization-only signal reported above bound; matched controls share visit type and year) | PASS |
| T126–T127 | — | **BLOCKED (implementation blocker A)**: V-10 (Workbench 2.0 access pattern) and V-11 (populated tables) unresolved; no SQL written | BLOCKED |
| T128 | `docs/verification/workbench-run-checklist.md` (12 steps with pass/fail fields; fr081 schema = `core/evidence.py::FR081Evidence`, data-model § 4) | prepared; execution blocked with T126–T127 | DONE (prepared) |

### Type 2 Diabetes (`kits/all_of_us/type_2_diabetes/`)

| Task | Artifact | Check | Result |
|---|---|---|---|
| T129–T131 | `phenotype.yaml`, `verification.yaml`, SourceRecords `ada_soc_2026_s2`, `kho_2012_emerge_t2d`; concepts `t2d_diagnosis`, `t1d_other_diabetes`, `diabetes_medications` (+ `hba1c`, `glucose`) | every item provisional with pending V-21/V-25 and candidate sources (not self-verified: ADA primary text not retrievable; PheKB logic not retrieved); `omop` realizations empty (P-5) | DONE (provisional) |
| T132 | `docs/features.md` V-24 review; prohibited `diabetic_complications`, `glucose_monitoring`, `diabetes_education` | each category has a decision and justification | DONE |
| T133 | `kit.yaml` temporal policy and `control_sampling` (matched, 2:1) | provisional (V-20) with rationale; `ckit docs --kit aou_t2d_current` regenerates the log | DONE (provisional) |
| T134 | `synthetic/golden/t2d/{cohort,features}.yaml` | load with provenance header; each fixture states which rules are provisional | DONE |
| T135 | `kits/all_of_us/type_2_diabetes/tests/test_kit.py` + generic `clinical_ml_kits/testing/reference_kit.py` | 14 tests failed before the kit existed | DONE |
| T136–T139 | concepts/realizations, `phenotype.yaml`, `kit.yaml`, `synthetic/generator_params/aou_t2d_current.yaml` | `ckit validate --level synthetic` PASS (12 provisional, 1 unverified = dataset.version); `--level workbench` fails listing them; partitions 474/87/105 positives | PASS |
| T140–T141 | KitDocs (6 files), generated `kit.ipynb` | `test_kitdocs_answers[type_2_diabetes]`, `ckit docs --check`, kit tests 14/14 incl. notebook execution, drift check | PASS |
| T142 | — | **DEFERRED (approval/Workbench blocker B)**: workbench level fails (12 provisional values) and AoU adapter blocked (V-10/V-11) | DEFERRED |
| T143 | `kits/catalog.yaml` entry: `candidate`, `verification_state: requires_verification`, blocker list | `ckit validate --all` PASS | DONE |

### Chronic Kidney Disease (`kits/all_of_us/chronic_kidney_disease/`)

| Task | Artifact | Check | Result |
|---|---|---|---|
| T144–T146 | `phenotype.yaml`, `verification.yaml`; SourceRecords `kdigo_ckd_2024` (definition and Table 1 extracted from the official PDF), `ckd_epi_2021`, `nadkarni_2014_emerge_ckd`; concepts `ckd_diagnosis`, `aki_diagnosis`, `dialysis_transplant`, `urine_albumin_protein` (+ `egfr`, `creatinine`) | provisional with pending V-22/V-25; `omop` empty | DONE (provisional) |
| T147 | `docs/features.md` V-24 review (BUN, cystatin C, dialysis/transplant, nephrology, kidney medications prohibited; potassium allowed with rationale) | every category decided with justification | DONE |
| T148 | temporal policy + matched sampling; chronicity index = date the 90-day span is first reached | provisional (V-20/V-22) | DONE (provisional) |
| — | **Framework change**: reusable `min_span` option on `has_event`/`measurement` (constitution XXIII) instead of kit code; contract + data-model updated | `tests/unit/cohort/test_rules.py::test_min_span_chronicity` (failed first) | PASS |
| T149–T150 | `synthetic/golden/ckd/{cohort,features}.yaml`; kit tests | 14 tests failed before the kit existed | DONE |
| T151–T154 | concepts, `phenotype.yaml`, `kit.yaml`, `synthetic/generator_params/aou_ckd_current.yaml` | `--level synthetic` PASS (19 provisional); positives 454/100/91 | PASS |
| T155–T156 | KitDocs, `kit.ipynb` | kit tests 14/14 incl. chronicity index and notebook execution; KitDocs and drift checks | PASS |
| T157 | — | **DEFERRED (B)** like T142 | DEFERRED |
| T158 | catalog entry `candidate`, `requires_verification`, blockers | `ckit validate --all` PASS | DONE |

### Hypertension (`kits/all_of_us/hypertension/`)

| Task | Artifact | Check | Result |
|---|---|---|---|
| T159–T161 | `phenotype.yaml`, `verification.yaml`; SourceRecords `acc_aha_bp_2017`, `teixeira_2017_htn`; concepts `htn_diagnosis`, `antihypertensive_medications`, `pregnancy_hypertension`, `secondary_hypertension` (+ BP concepts) | provisional with pending V-23/V-25; `omop` empty | DONE (provisional) |
| T162 | `docs/features.md` V-24 review (hypertensive heart/kidney disease and home BP monitoring prohibited; all antihypertensives prohibited; medication alone never a case; same-visit heart rate excluded on the index day) | every category decided | DONE |
| T163 | temporal policy + matched sampling | provisional (V-20) | DONE (provisional) |
| T164–T165 | `synthetic/golden/htn/{cohort,features}.yaml`; kit tests incl. beta-blocker-for-AF non-case | 15 tests failed before the kit existed | DONE |
| T166–T169 | concepts, `phenotype.yaml`, `kit.yaml`, `synthetic/generator_params/aou_htn_current.yaml` | `--level synthetic` PASS (19 provisional); positives 307/52/74. The visit-bias check first reported 0.706 (> 0.70) because the generator gave cases an extra pre-index visit; the generator was balanced (controls get the same −60-day reading). The remaining 0.693 reflects index-time selection of controls and is documented in `limitations.md` | PASS |
| T170–T171 | KitDocs, `kit.ipynb` | kit tests 15/15 incl. notebook execution; KitDocs/drift checks | PASS |
| T172 | — | **DEFERRED (B)** like T142 | DEFERRED |
| T173 | catalog entry `candidate`, `requires_verification`, blockers | `ckit validate --all` PASS | DONE |

### M4 integration

| Task | Artifact | Check | Result |
|---|---|---|---|
| T174 | `docs/reviews/m4-quickstart-run.md` | §§ 1–3 recorded pass/fail for all three kits (476 tests; synthetic level PASS, workbench/approval FAIL as expected; notebooks 10–15 s each; Colab-pinned stack PASS). Manual Colab smoke run NOT RUN (needs the `v0.1.0` tag pushed and a person in Colab) — linked remediation. Pre-commit `nbstripout` now uses `--keep-id` (it renumbered generated cell IDs, which would conflict with the drift check) | DONE (manual Colab pending) |

**M4 exit**: all three kits validate at the synthetic level, pass their kit tests (14/14/15), and run
end to end in synthetic mode. Approval status is reported honestly: all three remain
`requires_verification` (catalog `candidate` with blocker lists); T126–T127 blocked (V-10/V-11);
T142/T157/T172 deferred.
