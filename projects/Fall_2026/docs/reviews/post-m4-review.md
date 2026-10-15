# Post-Milestone-4 architecture review (mandatory stop gate)

- **Date**: 2026-10-15
- **Reviewer**: Claude Code (automated implementation agent), acting as recorder. Human maintainer
  sign-off is still required to accept this outcome (see § Outcome).
- **Scope**: Milestones 1–4 (`main` at `03bfcd9` plus the review commit); plan.md § 18; tasks T175–T183.
- **Evidence script**: per-kit checks were run by a script that loads each kit, runs its kit test
  suite (`pytest kits/all_of_us/<kit>/tests/test_kit.py -rA`), fits the baseline, runs one final
  evaluation, builds envelopes, and validates at the `approval` level. CI run
  [38807523512](https://github.com/CadenWondell/UNF-AIRO-Club/actions/runs/38807523512) (Python 3.10,
  3.13, Colab-pinned stack) is green on `03bfcd9`.

## Add-a-kit dry run (T175, quickstart § 5)

A fourth binary kit (`aou_scratch_dyslipidemia`, provisional dry-run values only, not a clinical
definition) was built on the local branch `scratch/add-a-kit-dry-run` (commit `eec4a88`, not merged
or pushed) by copying the T2D kit folder and changing only kit-specific artifacts.

| Check | Command / artifact | Result | Evidence |
|---|---|---|---|
| No shared-framework change | `git diff --stat main eec4a88 -- projects/Fall_2026/src` | PASS | empty (0 lines) |
| Changed paths are kit-specific only | `git diff --stat main eec4a88` (19 files) | PASS | `kits/all_of_us/scratch_dyslipidemia/**` (kit.yaml, phenotype.yaml, verification.yaml, docs ×6, tests incl. a kit-scoped golden fixture, kit.ipynb); `definitions/concepts/scratch_*.yaml` (2); `definitions/concept_sets/{synthetic,omop}/scratch_*/0.1.0.yaml` (4); `synthetic/generator_params/aou_scratch_dyslipidemia.yaml` |
| Synthetic level | `ckit validate kits/all_of_us/scratch_dyslipidemia --level synthetic` | PASS | 12 provisional, 1 unverified (`dataset.version`) |
| Notebook executes end to end | `ckit notebooks --kit aou_scratch_dyslipidemia`; `pytest --nbmake kits/all_of_us/scratch_dyslipidemia/kit.ipynb` | PASS | 1 passed (11.6 s); kit tests 4/4 incl. notebook execution; KitDocs answers check passed |

## § Reuse (T176)

| Check | Test / command / artifact | Result | Evidence |
|---|---|---|---|
| Shared Template A skeleton — T2D | `kit.yaml` `template_family`; notebook metadata `ckit.template_family` | PASS | `binary_tabular` / `binary_tabular` |
| Shared Template A skeleton — CKD | same | PASS | `binary_tabular` / `binary_tabular` |
| Shared Template A skeleton — HTN | same | PASS | `binary_tabular` / `binary_tabular` |
| Identical section structure (SC-013) | section headings of the three `kit.ipynb` | PASS | 13 identical headings in contract order |
| Notebook content checks — T2D | `notebooks.checks.check_notebook(kits/all_of_us/type_2_diabetes/kit.ipynb)` | PASS | 0 violations (visible LR `Pipeline`, `.fit`, grouped CV, no SQL/raw reads/split code/adapter imports) |
| Notebook content checks — CKD | same | PASS | 0 violations |
| Notebook content checks — HTN | same | PASS | 0 violations |
| Kit-difference scope | dry run above; `src/` contains no kit ids (`grep -r "aou_t2d\|aou_ckd\|aou_htn" src/` → none) | PASS | kits differ only in YAML definitions, logical concepts, sources, generator params, docs, tests |
| Import boundary | `tests/repo/test_import_boundaries.py::test_no_boundary_violations` | PASS | it also caught and blocked a `core → adapters` import during T097 |

Issue list: none.

## § ML validity (T177)

Kit-test node IDs are in `kits/all_of_us/<kit>/tests/test_kit.py`; all PASSED for all three kits.

| Check | T2D | CKD | HTN | Test node / evidence |
|---|---|---|---|---|
| Split integrity (one partition per person; one row per person; two-row person rejected) | PASS | PASS | PASS | `test_one_row_per_person_and_two_row_rejected`; framework `tests/leakage/test_split.py` (8 tests); partitions (n, positives): T2D train 1352/474, val 260/87, test 307/105; CKD 1167/454, 280/100, 277/91; HTN 911/307, 181/52, 207/74 |
| Grouped CV | PASS | PASS | PASS | `test_groups_and_grouped_cv`; `tests/leakage/test_grouped_cv.py` (GridSearchCV with groups sees train rows only; no group crosses folds; calibration folds respect groups); toy-notebook instrumentation (`tests/notebooks/test_toy_notebook_exec.py`) |
| Preprocessing isolation | PASS | PASS | PASS | `tests/leakage/test_preprocessing_isolation.py`; `kit.final_evaluation` ran `check_preprocessing_fit` on each kit's baseline without error; `tests/unit/core/test_final_evaluation.py::test_preprocessing_isolation_enforced` (leaky fit rejected) |
| Target leakage | PASS | PASS | PASS | `test_target_defining_features_excluded`, `test_label_defining_overlap_rejected`; no label-defining column in any kit's `X` |
| Label leakage (undeclared label sources) | PASS | PASS | PASS | `Kit.load` runs `check_label_sources` against case/control rule concepts; `tests/leakage/test_checks.py::test_label_leakage_undeclared_label_source` |
| Temporal cutoff | PASS | PASS | PASS | `test_feature_timeline_future_revealer_and_label_values_excluded` (post-index values never visible); lineage check in `Kit.load`; golden creatinine tests |
| Same-day / washout / index encounter | PASS | PASS | PASS | `test_same_day_rule` (index-day workup value visible only under the counterfactual `include` policy); `tests/unit/temporal/test_policy.py` 8-policy matrix |
| Test-partition guard | PASS | PASS | PASS | `tests/leakage/test_test_guard.py`; each kit's final evaluation logged once (`run_manifest.test_access_log`) |
| Index-visit bias | PASS (0.482) | PASS (0.631) | PASS (0.693) | `tests/leakage/test_index_visit_bias.py` (planted utilization signal detected); utilization-only validation AUROC per kit vs bound 0.70 |

Issue list:
1. HTN utilization-only AUROC 0.693 is close to the 0.70 bound. Diagnosis: controls must accumulate
   two normal readings before eligibility, so they are indexed later with more prior visits (mean
   2.2 vs 1.3 visits in the prior year). This is index-time selection inherent in the provisional
   phenotype, not a framework defect; it is documented in `hypertension/docs/limitations.md`. Not
   blocking.

## § Prediction type (T178)

| Check | T2D | CKD | HTN | Evidence |
|---|---|---|---|---|
| `prediction_type` | PASS | PASS | PASS | `current_state` (schema test `test_kit_schema.py` rejects horizons on current_state) |
| `horizon` null | PASS | PASS | PASS | kit `horizon: None`; envelopes `horizon: null` |
| No future-risk terms in configs / notebooks / docs | PASS | PASS | PASS | regex `future_risk\|will develop\|risk of developing\|onset within\|incident ` over kit.yaml, phenotype.yaml, KitDocs, kit.ipynb: no matches |

Issue list: none.

## § Standard output (T178)

| Check | T2D | CKD | HTN | Evidence |
|---|---|---|---|---|
| Envelope validity v1.0.0 | PASS | PASS | PASS | 5 envelopes per kit validated by `PredictionEnvelope`; `test_envelopes`; `tests/contract/test_envelope.py` (24 tests) |
| `probability_basis: development_sample` | PASS | PASS | PASS | every envelope |
| No person ID / group key in output | PASS | PASS | PASS | `tests/unit/prediction/test_to_envelopes.py` (group keys absent from serialized envelopes) |

Issue list: none.

## § Test-first (T179)

| Check | Command | Result | Evidence |
|---|---|---|---|
| Golden-patient suite | `pytest tests/unit/features tests/unit/temporal tests/unit/cohort tests/unit/synthetic` | PASS | creatinine and same-day golden values reproduced by both entry points |
| Framework suite | `uv run pytest` | PASS | 476 passed (quickstart run); CI 38807523512 green on 3.10 / 3.13 / Colab stack |
| T2D kit suite | `pytest kits/all_of_us/type_2_diabetes` | PASS | 14/14 |
| CKD kit suite | `pytest kits/all_of_us/chronic_kidney_disease` | PASS | 14/14 |
| HTN kit suite | `pytest kits/all_of_us/hypertension` | PASS | 15/15 |
| Notebook execution | `pytest --nbmake kits/` | PASS | 3 kit notebooks 10–15 s each + setup check; also from an installed wheel outside the repository (Colab install path) |
| Notebook drift | `ckit notebooks --check` (+ `--root tests/fixtures`) | PASS | no drift |
| Docs drift | `ckit docs --check` (+ fixtures) | PASS | logs current |
| Test-before-implementation sample | git history | PASS (with note) | Each task's tests were written and run to an expected failure before implementation (recorded per task in `docs/reviews/task-evidence.md`). Commit `477d8ad` holds the generator tests failing by design before `1e824bc` implemented the generator; most other commits bundle tests with implementation (e.g. `2107c52`: 83 test files / 22 source files; `f337dc1`: 9 / 7; `0fc6e80`: 6 / 11; each kit commit adds its kit test file). Exceptions recorded honestly: the KitDocs README helper (T054) and traceability (T081) were implemented with earlier tasks before their dedicated tests |

Issue list: none blocking (the two ordering exceptions are documented).

## § Clinical evidence (T180)

| Check | T2D | CKD | HTN | Evidence |
|---|---|---|---|---|
| `ckit validate --level approval` | FAIL as required | FAIL as required | FAIL as required | 60 / 68 / 70 open items listed (provisional values, missing verified `omop` realizations, no review sign-off, no FR-081 evidence) |
| No kit approved with provisional/unverified items | PASS | PASS | PASS | status `requires_verification`; catalog `candidate` with blocker lists; `test_approved_rejected_while_provisional` (P-4) |
| P-8 traceability | PASS | PASS | PASS | 13 / 13 / 14 features traced (feature → logical concept → synthetic realization → table → SourceRecord); `omop` chains fail at the realization link as designed |
| Generated verification log current | PASS | PASS | PASS | `ckit docs --check` |
| Provisional / unverified counts | 12 / 1 | 19 / 1 | 19 / 1 | listed in each `docs/verification_log.md` |
| FR-081 evidence for approved kits | N/A | N/A | N/A | no kit approved; Workbench runs T142/T157/T172 deferred |

Issue list:
1. Clinical definitions (V-20, V-21, V-22, V-23, V-24, V-25) are not verified: primary ADA and ACC/AHA
   texts could not be retrieved automatically; PheKB algorithm logic was not retrieved; no OMOP
   concept IDs were selected. All values are provisional and labeled. **Approval blocker** (not an
   architecture defect).

## § Data / privacy (T181)

| Check | Command / artifact | Result | Evidence |
|---|---|---|---|
| Data guard | `python tests/repo/data_guard.py --all` | PASS | exit 0 over all committable files; pre-commit hook blocks a planted `persons.csv` |
| Golden fixture headers and `SYN-` IDs | load every `*/golden/*.yaml` with `load_golden` | PASS | 11 fixtures |
| Synthetic realizations use `SYN-` codes + header (P-5) | `check_definitions` (project and fixtures) | PASS | 0 errors |
| Generator settings headers | `load_params` over every `generator_params/*.yaml` | PASS | 8 files: artificial, not clinically realistic, not derived from participant data |
| No participant data or group keys in the repository | grep for 24-hex group-key-like strings and non-`SYN-` person IDs in tracked files | PASS | none |
| V-03-compliant exports | `completion/suppression.py`; `tests/unit/completion/test_suppression.py` | PASS | no Workbench export has occurred (Workbench runs deferred) |
| Policy matrix / no egress assumptions | `tests/unit/completion/test_policy_matrix.py`, `tests/unit/data/test_policy.py`, `tests/unit/adapters/test_aou_boundary.py`, `tests/integration/test_load_kit.py` | PASS | 50 passed: portable save refused in the Workbench policy; checkout writes refused; All of Us mode refused outside a verified Workbench before data access (fails closed while V-10 is unresolved) |

Issue list: none.

## § Milestone discipline (T182)

`git diff --stat main eec4a88 -- projects/Fall_2026/src` output: *(empty)*.

| Check | Command / artifact | Result | Evidence |
|---|---|---|---|
| Fourth similar kit needs only kit-specific artifacts | dry run (T175) | PASS | see table above |
| Required shared-framework changes for a fourth kit | — | PASS | **none** |
| RuleExpr sufficiency | reference kits + dry run | PASS (yes) | yes, after one reusable extension made during M4: `min_span` on `has_event`/`measurement` (KDIGO chronicity), added through review as a generic predicate option (constitution XXIII) rather than kit code |
| No M5 work started | git history; tasks.md | PASS | only M1–M4 tasks implemented |

Friction points and abstraction notes:
1. **Chronicity** required the `min_span` predicate option (added in CKD work; contract and data-model updated).
2. **Index-visit bias** required an optional `visit_bias_check` block (ADR-002); the HTN result shows
   phenotype-driven index selection can create utilization differences — worth a dedicated review
   when more kits are added.
3. **Kit test duplication** was avoided with a generic `clinical_ml_kits.testing.reference_kit` module;
   kit test files hold only kit-specific expectations.
4. **Library drift**: `None` categories on older pandas and the scikit-learn `penalty` deprecation
   (cap `<1.10`) surfaced only under multi-version testing; the Colab-pinned CI job now guards this.
5. The All of Us adapter is a fail-closed boundary only; its query layer awaits V-10/V-11.

## Constitution gate results

| Gate | Result | Basis |
|---|---|---|
| 1 Reuse | PASS | § Reuse; dry run |
| 2 ML validity | PASS | § ML validity (all checks green on all kits) |
| 3 Prediction type | PASS | § Prediction type |
| 4 Test first | PASS | § Test-first (ordering exceptions documented) |
| 5 Clinical evidence | PASS (gating works); clinical verification open | § Clinical evidence: no approval with unverified items; every open item listed |
| 6 Standard output | PASS | § Standard output |
| 7 Data / privacy | PASS | § Data / privacy |
| 8 Milestone discipline | PASS | § Milestone discipline |

## plan.md § 18 checklist

| # | Item | Result |
|---|---|---|
| 1 | Same Template A for all kits | PASS |
| 2 | No duplicated framework logic | PASS |
| 3 | Kit differences are configuration/definitions | PASS |
| 4 | AoU code only under `adapters/all_of_us/` | PASS |
| 5 | No patient crosses partitions | PASS |
| 6 | Preprocessing fit on train only | PASS |
| 7 | Temporal restrictions work | PASS |
| 8 | Same-day and workup rules work | PASS |
| 9 | Target-defining features excluded | PASS |
| 10 | Golden-patient suites pass | PASS |
| 11 | Provenance P-1…P-11 clean | PASS |
| 12 | Definitions verified before approval | PASS (none approved) |
| 13 | Envelopes conform to v1.0.0 | PASS |
| 14 | Synthetic mode runs in Colab | **CONDITIONAL**: nbmake PASS; Colab-pinned stack PASS (CI + local); installed-wheel run outside the repository PASS; **manual Colab smoke run not yet performed** |
| 15 | All three kits run end to end | PASS (synthetic); Workbench runs deferred until definitions are verified |
| 16 | Add-a-kit dry run needs no `src/` change | PASS |

## Outcome

**CONDITIONAL PASS** — 2026-10-15, recorded by Claude Code; requires maintainer sign-off.

All eight constitution gates pass and the architecture needs no revision. The conditions are external
actions that the implementation agent cannot perform:

| # | Remediation | Owner | Blocks M5? |
|---|---|---|---|
| R1 | Push the `v0.1.0` tag (the notebooks' pinned install) and run each kit notebook once in a fresh Google Colab runtime; record the Colab Python/library versions in `docs/reviews/m4-quickstart-run.md` | maintainer | **blocks M5** (plan § 18 item 14) |
| R2 | Maintainer sign-off on this review | maintainer | **blocks M5** |
| R3 | Resolve V-10 / V-11 / V-12 inside a Workbench 2.0 JupyterLab app; then T126–T128 and the Workbench runs T142/T157/T172 | maintainer with Workbench access | does not block M5 planning; blocks any kit approval and M5 FR-081 evaluations |
| R4 | Clinical reviewer verification of V-20–V-25 for the three kits | clinical reviewer | does not block M5 planning; blocks approval |
| R5 | All of Us support ticket for V-01 / V-02 / V-04 | maintainer | no |

Remediation performed within M1–M4 during the review: the CI `colab-stack` job now also executes the
three kit notebooks from the installed wheel outside the repository (the Colab install path), after
a local run of the same scenario passed (T2D 38.9 s, CKD 12.8 s, HTN 11.4 s).

Constitution/plan changes warranted: none beyond the recorded contract additions (`min_span`,
`visit_bias_check`).

**STOP**: Milestone 5 must not start until R1 and R2 are closed.
