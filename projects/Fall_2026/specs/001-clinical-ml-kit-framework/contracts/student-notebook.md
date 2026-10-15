# Contract: Student Kit Notebook (`kit.ipynb`)

Every kit ships one generated, **executable** Jupyter notebook that contains the visible Python ML
workflow. Shared modules provide infrastructure; the notebook shows and runs the machine
learning.

## Core rules
1. **Executable ML workflow is visible in the notebook.** The notebook contains real Python code
   to load data, inspect it, run EDA, build and fit the baseline, predict, evaluate, plot, run
   calibration and explainability, experiment, tune, compare, and complete the model.
2. **The baseline runs end to end with no student edits.** "Run all" on a fresh runtime in synthetic
   mode completes and produces baseline results. No `TODO`, `...`, or `NotImplementedError` appears
   in any baseline or framework cell.
3. **Standard libraries only for models.** Baselines and suggested student models use standard
   estimators (scikit-learn for traditional ML; PyTorch + torchvision for future deep-learning
   kits). Students are never asked to implement learning algorithms, optimizers, backpropagation,
   convolution, attention, or model internals from equations.
4. **No duplicated infrastructure.** Data access, OMOP mapping, cohort/label construction, feature
   extraction, splitting, leakage checks, prediction-envelope building, provenance validation, and
   completion/serialization are **imported** from `clinical_ml_kits`, never re-implemented in a cell.
5. **Data access goes through the framework.** Notebooks never query All of Us tables, read raw data
   files, or construct splits themselves.

## Cell roles (metadata tag `ckit_role`)
| Role | Banner | Content | Editable? |
|---|---|---|---|
| `framework` | "Framework — do not edit" | Setup/install, `load_kit`, leakage checks, `final_evaluation`, completion | No (the builder can restore it; its hash is recorded) |
| `baseline` | "Baseline — working example" | Explicit scikit-learn code that builds, fits, predicts, and evaluates the baseline | Readable and modifiable; students are directed to copy it into student cells rather than change it, so the comparison point is preserved |
| `student` | "Your work" | Starter code (runnable), e.g., an alternative estimator, a tuning grid | Yes |
| `markdown` | — | Clinical background, construction narrative, expected outputs, interpretation prompts | Generated from KitDocs |

## Required sections and representative code
Generated from the template-family skeleton. Values (feature lists, baseline parameters, metric
lists, threshold rule) are rendered **literally** from `kit.yaml`, so the code reads naturally.

| § | Section | Representative code shown in cells |
|---|---|---|
| 0 | Setup | `%pip install "clinical-ml-kits @ git+…@vX.Y.Z"`; `import numpy as np, pandas as pd, matplotlib.pyplot as plt`; `from clinical_ml_kits import load_kit`; `kit = load_kit("aou_t2d_current", data_source="synthetic")` |
| 1 | Clinical problem | Markdown; `kit.describe()` prints the question, target, prediction type, and excluded features |
| 2 | Dataset and cohort | `data = kit.load()`; `data.train.X.head()`; `data.summary()` (sizes, prevalence; filtered per the V-03 rule in the Workbench) |
| 3 | EDA | pandas/matplotlib code: distributions, missingness table (`data.train.X.isna().mean()`), outcome by feature |
| 4 | Preprocessing | `from clinical_ml_kits.preprocessing import make_preprocessor`; `preprocessor = make_preprocessor(kit.feature_spec)`; `preprocessor` displayed; Markdown explains median imputation, missingness indicators, and scaling |
| 5 | Baseline model | `from sklearn.pipeline import Pipeline`; `from sklearn.linear_model import LogisticRegression`; `baseline = Pipeline([("preprocess", preprocessor), ("model", LogisticRegression(C=1.0, penalty="l2", solver="lbfgs", max_iter=1000))])`; `baseline.fit(data.train.X, data.train.y)`; `val_proba = baseline.predict_proba(data.validation.X)[:, 1]` |
| 6 | Evaluate the baseline | `from clinical_ml_kits.evaluation import evaluate_binary, plot_roc_pr`; `baseline_results = evaluate_binary(data.validation.y, val_proba, threshold_rule="youden")`; `baseline_results.table()`; `plot_roc_pr(...)` |
| 7 | Your model | Starter: `from sklearn.ensemble import RandomForestClassifier` in a `Pipeline` with the same preprocessor; listed alternatives: `HistGradientBoostingClassifier`, `GradientBoostingClassifier`, `SVC(probability=True)`, `KNeighborsClassifier` |
| 8 | Hyperparameter tuning | `from sklearn.model_selection import GridSearchCV`; `cv = kit.cv_splitter()` (patient-grouped folds within train); `GridSearchCV(model, param_grid, cv=cv, scoring="average_precision")`; `search.fit(data.train.X, data.train.y, groups=data.train.groups)` |
| 9 | Model comparison | `compare_models({"baseline": baseline, "student": best}, data.validation)` → table and plots |
| 10 | Calibration | `plot_calibration(data.validation.y, proba)`; Brier score, calibration slope/intercept. Optional recalibration only through the grouped pattern selected by V-14 (e.g., `kit.calibrate_grouped(model, method="sigmoid")`, which fits the calibrator on out-of-fold predictions from `kit.cv_splitter()` with `groups`), never `CalibratedClassifierCV` with default folds. Markdown explains **sampled development prevalence vs population prevalence**: probabilities reflect the kit's control sampling and are not population disease probabilities |
| 11 | Explainability | Baseline: `coefficient_table(baseline)`; any model: `sklearn.inspection.permutation_importance(model, data.validation.X, data.validation.y)` |
| 12 | Final selection and completion | `final = best`; `report = kit.final_evaluation(final)` (test, once, logged); `envelopes = kit.to_envelopes(final, data.validation.X.head())`; `kit.complete(final)` (policy-gated save) |

## Helper boundary (what is a shared helper vs visible code)
- **Visible code**: estimator choice and parameters, `Pipeline` assembly, `.fit`, `.predict_proba`,
  tuning setup, plotting calls, comparisons.
- **Shared helpers** (importable, tested, called from cells): `load_kit`, `kit.load`,
  `make_preprocessor`, `kit.cv_splitter`, `evaluate_binary`, plotting helpers, `coefficient_table`,
  `compare_models`, `kit.final_evaluation`, `kit.to_envelopes`, `kit.complete`.
- A helper is added only when the same logic would otherwise appear in more than one kit notebook
  **and** it is infrastructure or evaluation logic, not the student's modeling choice.

## Grouping and model-selection safety
- `data.<partition>.groups` exists in every execution mode. It is an opaque key, never displayed,
  never a feature, and never in outputs.
- Every model-selection or resampling call in generated cells uses `cv=kit.cv_splitter()` **and**
  passes `groups=` (or uses a framework helper that does). Rejected patterns: `GridSearchCV`,
  `RandomizedSearchCV`, `HalvingGridSearchCV`, `HalvingRandomSearchCV`, `cross_val_score`,
  `cross_validate`, `cross_val_predict`, `learning_curve`, `validation_curve`, and
  `CalibratedClassifierCV` with an integer, missing, or non-grouped `cv`, or without groups.
- Reference kits additionally satisfy the one-row-per-person invariant (data-model § 4), so even an
  accidental default fold cannot split one patient's rows. The guard still applies so the rule
  remains safe for future multi-row templates.

## Provisional values
Sections 1, 2, and the excluded-features explanation render every provisional value (contracts/kit-definition.md)
with the banner "PROVISIONAL — synthetic-only, not an approved clinical definition". Workbench
generation requires the `workbench` validation level.

## Validation (tests/notebooks)
- Runs end to end under nbmake in synthetic mode for every kit.
- Structure: all sections present in order; every cell has a `ckit_role`.
- Content checks: `baseline` cells contain an estimator construction and a `.fit(` call; no cell
  contains a direct SQL/BigQuery call, raw-data file reads, or split construction; no
  placeholder tokens in `framework` or `baseline` cells; no unsafe model-selection or CV call
  (see above); `groups` is never displayed or added to `X`.
- Baseline/config consistency: the parameters rendered in the baseline cell equal `kit.yaml`
  `baseline.params`.
- Drift: regenerating from template + kit files reproduces the committed notebook (outputs stripped).
