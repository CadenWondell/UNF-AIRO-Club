# Quickstart Validation Guide: Milestones 1–4

Runnable scenarios that prove the framework works end to end. Commands are run from
`projects/Fall_2026/`. They describe the intended interface; nothing exists until implementation.

## Prerequisites
- Python ≥ 3.10; `uv` (maintainers) or `pip` (students).
- No All of Us access needed for §§ 1–3. § 4 requires a registered Workbench workspace with the
  appropriate access tier.

## 1. Maintainer setup and checks (M1)
```bash
uv sync --all-extras          # dev environment from uv.lock
uv run pre-commit install     # ruff, nbstripout, data guard
uv run pytest                 # unit + contract + golden-patient tests
uv run ckit validate --all    # kit definitions, provenance (P-1..P-11), catalog
uv run ckit notebooks --check # regenerated notebooks match committed ones (drift)
uv run ckit docs --check      # generated verification logs are current
```
**Expected**: all pass. `ckit validate --level synthetic` passes for the reference kits;
`--level workbench` and `--level approval` fail, listing each provisional and unverified item;
the kits report `requires_verification` and `approved` is refused. `uv run ckit docs --check` confirms
each generated `verification_log.md` is current. (Generation commands need the `[dev]` extra;
student notebooks do not.)

## 2. Leakage protections fire (M2)
```bash
uv run pytest tests/leakage -k "golden"
```
**Expected**: the golden-patient values in [contracts/patient-feature-api.md](contracts/patient-feature-api.md)
are reproduced by both the patient view and the bulk builder. Deliberately broken fixtures
(post-index row, cross-partition patient, prohibited feature, label-source feature,
same-day workup row, scaler fit on all rows) each raise the named error (SC-005).

## 3. Student flow in synthetic mode (M3–M4) — Colab or local Jupyter
1. Open `kits/all_of_us/type_2_diabetes/kit.ipynb` in Colab.
2. Run the setup cell (installs the pinned framework tag, selects `data_source: synthetic`).
3. Run all cells.

**Expected**: without any edits, the notebook's visible Python code loads the kit's artificial synthetic
population (from `synthetic/generator_params/<kit_id>.yaml`, not golden fixtures), runs the EDA,
builds the scikit-learn baseline `Pipeline` (preprocessor + `LogisticRegression`), fits it, predicts,
and shows validation metrics (AUROC, AUPRC, sensitivity/specificity at the declared threshold,
confusion matrix, Brier score, reliability plot) and coefficient and permutation-importance tables;
the starter student cell (e.g., `RandomForestClassifier` in the same pipeline) and the
`GridSearchCV` cell with `kit.cv_splitter()` also run; cell banners distinguish framework, baseline,
and student code;
`kit.final_evaluation(model)` runs once and logs test access; a valid envelope is produced; a
portable demo model can be saved because the environment is synthetic; provisional values appear
with the "PROVISIONAL — synthetic-only" banner; the calibration section explains sampled vs
population prevalence. Repeat for CKD and Hypertension: identical section structure (SC-013).
CI equivalent: `uv run pytest --nbmake kits/`.

## 4. Workbench verification run (M4; manual, inside the Workbench only)
1. In a Workbench Jupyter environment, install the pinned tag with the `[aou]` extra.
2. Open the same `kit.ipynb`; set `data_source: all_of_us`.
3. Run all cells.

**Prerequisite**: `ckit validate --level workbench` passes (no provisional values) and V-03 is resolved.
**Expected**: the adapter initializes only inside the Workbench; the cohort, features, and baseline run
on real data; `completion.save_model(..., portable=True)` is **refused**; a CompletionRecord and
the FR-081 evidence are written to the workspace with aggregates filtered per the V-03 rule; no
file is written into the git checkout. Only V-03-permitted aggregates are copied into
`kits/<kit>/evidence/fr081.yaml` and `verification.yaml` notes; `verification_log.md` is then
regenerated, never hand-edited.

## 5. Add-a-kit dry run (post-M4 review)
Copy a reference kit's folder into a scratch kit and add or change only kit-specific artifacts:
`kit.yaml`, `phenotype.yaml`, logical concepts (`definitions/concepts/`), concept-set realizations
(`synthetic`, plus `omop` where needed), synthetic population settings
(`synthetic/generator_params/<kit_id>.yaml`: artificial, not clinically realistic, not derived from
participant data), KitDocs, and kit tests. Regenerate its notebook
(`uv run ckit notebooks --kit <scratch>`), then run §§ 1 and 3.
**Expected**: no change under `src/` is needed (SC-003); `ckit validate --level synthetic` passes; the
regenerated notebook contains the new kit's features and baseline code and runs end to end on its
synthetic population.
