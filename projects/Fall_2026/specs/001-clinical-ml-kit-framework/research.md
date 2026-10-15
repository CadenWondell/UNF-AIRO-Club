# Phase 0 Research: Clinical ML Kit Framework

**Date**: 2026-10-15 | **Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)

Each entry: **Decision**, **Rationale**, **Alternatives considered**. Items that depend on
external facts not verifiable during planning are flagged `VERIFY` and listed in
plan.md § 21 (Remaining verification tasks).

---

## R-01 Language and runtime

- **Decision**: Python, `requires-python >= 3.10`; CI tests on 3.10 and the current Colab
  default (3.12 at time of writing — `VERIFY` at M1 start).
- **Rationale**: Jupyter/Colab requirement (FR-140) implies Python. 3.10 is a conservative floor
  that is expected to cover the All of Us Researcher Workbench Jupyter image as well as Colab.
- **Alternatives**: R (poorer Colab support, mismatch with student ML ecosystem); pinning one
  exact Python version (breaks when Colab upgrades).
- `VERIFY` (V-12): Python version and preinstalled package versions in the Workbench Jupyter image.

## R-02 Packaging and dependency management

- **Decision**: One installable package, `clinical_ml_kits`, defined in `pyproject.toml`
  (hatchling build backend). Students install with plain `pip install` of a pinned git tag inside
  the notebook's first cell. Maintainers use `uv` for a locked dev environment (`uv.lock`). Runtime
  dependencies are kept small and use compatible-range pins (`>=x.y,<next-major`), so the package
  coexists with Colab's and the Workbench's preinstalled libraries.
  Optional extra `[aou]` adds only what the All of Us adapter needs. Notebook **generation**
  (`ckit notebooks`, `ckit docs`) needs the `[dev]` extra (nbformat); the builder imports nbformat
  lazily, so importing `clinical_ml_kits` and running student notebooks never requires generation
  tooling.
- **Rationale**: `pip install git+…@vX.Y.Z` works in both Colab and Jupyter without extra
  tooling; a pinned tag fixes the framework version per semester (reproducibility, protects
  infrastructure from edits). `uv` gives maintainers fast, reproducible dev installs without
  imposing it on students.
- **Alternatives**: Poetry (heavier, students don't need it); conda (slow in Colab, not
  needed); vendoring framework code into notebooks (violates FR-147); publishing to PyPI
  (unnecessary for a course; possible later).

## R-03 Kit definition format and validation

- **Decision**: YAML kit definitions validated by Pydantic v2 models. JSON Schema is generated
  from the Pydantic models and published under `docs/schemas/` for reviewers and editors.
- **Rationale**: YAML is human-readable and supports comments that reviewers can read;
  Pydantic gives typed models, clear error messages (FR-011), and cross-field validators
  (e.g., horizon required iff `future_risk`; prohibited ∩ required features = ∅). One source of
  truth: schema follows the code.
- **Alternatives**:
  - TOML — good for flat config, awkward for nested rule lists (cohort/exclusion rules).
  - JSON — no comments, noisy for humans.
  - Python dataclass configs — invites logic in config, harder for non-programmer reviewers,
    violates "definitions visible, not buried in code" (FR-155).
  - Hand-written JSON Schema + jsonschema lib — duplicated truth, weaker error messages.

## R-04 Data representation

- **Decision**: pandas DataFrames for tabular data; the canonical clinical representation is
  a long-format **observation table** (one row per observation) plus a **person table**.
  Bulk feature extraction is vectorized (groupby/merge), never per-patient Python loops.
- **Rationale**: pandas is preinstalled in Colab and the Workbench and familiar to students.
  Long format maps naturally onto OMOP domain tables and preserves timestamp, unit,
  source domain, and mapping version on every value (FR-153).
- **Alternatives**: Polars (faster, but less familiar to students and may not be
  preinstalled; can be adopted internally later behind the same API); wide tables at the adapter
  boundary (loses provenance and timing).

## R-05 Baseline ML stack

- **Decision**: scikit-learn: `Pipeline` + `ColumnTransformer` + `LogisticRegression`;
  `sklearn.calibration.calibration_curve`, `brier_score_loss`; permutation importance from
  `sklearn.inspection`. Plotting with matplotlib.
- **Rationale**: Understandable, reproducible baseline (FR-045). Pipelines make train-only
  fitting structural (FR-054). Everything is preinstalled in Colab.
- **Student-model policy**: Students use standard estimators — `LogisticRegression`,
  `RandomForestClassifier`, `GradientBoostingClassifier`/`HistGradientBoostingClassifier`, `SVC`,
  `KNeighborsClassifier`, and other scikit-learn estimators — and never implement algorithms from
  equations. Core stack: Python, NumPy, pandas, Matplotlib, scikit-learn.
- **Alternatives**: statsmodels for the LR baseline (better inference output, but weaker
  integration with pipelines); SHAP (heavy dependency, may have version conflicts; students can
  add it in their own work).

## R-06 Explainability baseline

- **Decision**: Template A provides (1) standardized LR coefficients mapped back to feature
  names, including missingness indicators, and (2) permutation importance on the validation
  partition. Per-prediction top features in the envelope are signed coefficient × standardized
  value contributions (exact for a linear model).
- **Rationale**: Exact and cheap for LR; no extra dependency; easy to teach.
- **Alternatives**: SHAP (deferred to student work / later templates).

## R-07 Testing and notebook validation

- **Decision**: `pytest` for all tests; `nbmake` runs every kit notebook end-to-end in synthetic
  mode in CI; `nbstripout` (pre-commit) strips outputs from committed notebooks; a custom pytest
  check validates notebook structure (section headings, cell tags) against the template.
- **Rationale**: One test runner for code and notebooks; standard, well-supported tools.
- **Alternatives**: `nbval` (compares outputs — brittle with plots); papermill (parameterization
  is not needed because the adapter is selected by configuration).

## R-08 Lint, format, types

- **Decision**: `ruff` (lint + format), `mypy` on `src/` (strict on `core`, `prediction`,
  `provenance`, `leakage`; standard elsewhere), `pre-commit` to run ruff, nbstripout, and a
  repository data guard.
- **Rationale**: Minimal tool count; ruff replaces flake8/isort/black.
- **Alternatives**: black + flake8 + isort (three tools instead of one); pyright (mypy is more
  common in course settings).

## R-09 CI

- **Decision**: GitHub Actions workflow at the repository root (`.github/workflows/`), scoped to
  `projects/Fall_2026/**` with that directory as `working-directory`. Jobs: lint/type → unit and
  contract tests → kit-definition and provenance validation → notebooks (synthetic mode) →
  data guard.
- **Rationale**: The repository is already on GitHub (`CadenWondell/UNF-AIRO-Club`); this is
  free for public repositories.
- **Alternatives**: none needed.

## R-10 Patient split strategy

- **Decision**: **Deterministic hash-based assignment.** partition = f(SHA-256(`split_salt` +
  `person_id`)), mapped to train/validation/test by configured fractions (default 70/15/15).
  Each run records a **split manifest digest** (hash of the sorted assignment) and per-partition
  prevalence in its run manifest. In the Workbench, the assignment table may additionally be
  persisted inside the workspace (never in the repo).
- **Tradeoffs**:
  | Approach | Pros | Cons |
  |---|---|---|
  | Hash-based (chosen) | No stored artifact needed (works with synthetic and AoU alike; nothing participant-level is committed); stable per patient when the cohort changes; trivially reproducible | Not stratified, so prevalence can drift in small cohorts |
  | Persisted assignment file | Exact, auditable; can be stratified | For AoU it can't live in the repo; has to be managed per environment; goes stale when the cohort changes |
  | Seeded `StratifiedGroupKFold`-style split | Stratified | Assignments shift whenever the cohort changes; depends on library version |
- **Mitigation for the hash-based downside**: validation fails when any partition's
  positive count is below a configured minimum, and warns when its prevalence deviates from overall
  prevalence by more than a configured tolerance.
- **Salt discipline**: the salt is fixed and versioned per kit (`split.salt`, `salt_version`,
  `salt_history`). A change requires a version bump and a documented reason. Changing the salt to
  get a more favorable outcome balance is prohibited, because that would amount to cherry-picking
  the test set. If a partition fails the minimum-positives check, the remedy is to revisit the
  cohort or fractions, documented as a method decision, not to try more salts.
- **Group key**: the same hashing approach, with a distinct prefix, yields the opaque
  `groups` key used by grouped CV in every execution mode (data-model § 4).
- Specialty datasets: the hash runs on the dataset's patient/group key, so multiple images or
  signals per patient stay together. Where a dataset publishes official patient-safe folds
  (e.g., PTB-XL's recommended folds — `VERIFY` at specialty evaluation), the adapter may supply
  `official_split` and the kit declares which strategy it uses.

## R-11 Test-set protection

- **Decision**: `KitData` exposes `train` and `validation` freely; the test partition is
  available only through `kit.final_evaluation(model)`, which runs evaluation once,
  records a timestamped test-access entry in the run manifest, and warns on repeat calls.
  Raw test rows are not returned to the notebook.
- **Rationale**: Enforced by the API rather than by instructions (spec: "fail loudly";
  constitution VI).
- **Alternatives**: documentation-only (rejected); hard single-use lock (too brittle when Colab
  restarts).

## R-12 Temporal cutoff enforcement

- **Decision**: Enforcement by construction plus verification:
  1. The adapter filters by `observation_time < cutoff` (pushes the filter into the query
     where possible).
  2. `PatientTimeline.as_of(index_time, temporal_policy)` returns a `CutoffView` that physically
     contains only permitted observations; every feature function operates on views.
  3. After extraction, the leakage checker asserts that every source observation contributing to
     every feature has a timestamp < its effective cutoff (lineage check over the provenance
     columns).
- **Same-day and workup leakage**: `TemporalPolicy` computes an *effective cutoff* per
  domain/concept set. It handles: same-day inclusion (`include` | `exclude_index_day`),
  `washout` before index, exclusion of the index encounter, and windowed exclusions around the
  index for named concept sets or domains (e.g., "exclude procedures in concept set X within ±N
  days"). The policy has **no implicit default**: every kit must declare it explicitly
  (validation error otherwise). See [contracts/kit-definition.md](contracts/kit-definition.md).
- **Rationale**: `feature_time <= index_time` alone is insufficient (spec FR-137; plan input § 6).
- **Alternatives**: post-hoc filtering only (silent if forgotten); trusting the adapter only
  (no defense in depth).

## R-13 Target and label leakage detection

- **Decision**: Phenotype definitions declare their **label-defining logical concepts**; the
  feature registry declares each feature's concept sets. Validation computes the intersection of
  model input features with label-defining logical concepts plus explicit `prohibited` entries and
  fails unless a `justified_inclusion` entry with rationale exists. Label construction and
  feature construction run in separate modules (`cohort/` vs `features/`) that share only the
  adapter; tests assert that features are unchanged when the label function is altered.
- **Rationale**: Mechanically checkable (FR-133, FR-052/053).

## R-14 Serialization and environment policy

- **Decision**: Serialization uses `joblib` (ships with scikit-learn) plus a JSON metadata
  sidecar (run manifest + envelope schema version). Every write goes through
  `completion.save_model(...)`, which consults the active `DataEnvironmentPolicy`:
  - `synthetic` / `public`: serialization and portable artifacts allowed (subject to dataset
    licenses).
  - `all_of_us_workbench`: saving within the workspace is allowed (for the student's own
    reuse); producing a **portable artifact** is refused. A **completion record** (metrics,
    metadata, kit-definition hash, no participant rows, aggregates filtered per R-15/V-03) is the
    deliverable.
- **Rationale**: FR-095–FR-099; the architecture never depends on model export.
- **Alternatives**: `skops` (safer loading format, extra dependency — reconsider for demo
  models distributed to the dashboard); ONNX (unnecessary for M1–4).

## R-15 Aggregate output from the Workbench (dissemination filter, pending V-03)

- **Decision**: Any aggregate leaving the Workbench (completion record, portable project
  definition, FR-081 evidence, verification notes, README statistics, notebook outputs, figures,
  CI artifacts, or anything committed to the public GitHub repository) passes through a
  dissemination filter. The **small-count dissemination threshold and its scope are pending
  verification task V-03**; the architecture contains no threshold value. Until V-03 is resolved,
  Workbench completion records and evidence exports are blocked with `PendingVerification("V-03")`.
  In-session display inside the Workbench is unaffected.
- **Rationale**: The All of Us Data and Statistics Dissemination Policy restricts sharing granular
  aggregate statistics. Confusion matrices, calibration bins, subgroup tables, and cohort
  descriptions are exactly such statistics, and being aggregate does not by itself make a result
  publishable.
- `VERIFY` (V-03): exact threshold; which outputs it covers (including derived metrics on small
  subgroups); whether committing aggregates to a public repository requires anything beyond the
  threshold.

## R-16 Notebook strategy

- **Decision**: **One main notebook per kit** (`kit.ipynb`) organized as 12 numbered sections
  matching the FR-040 workflow, plus a short `00_setup_check.ipynb` for environment
  diagnostics. Notebooks are **generated** from one shared notebook template per template
  family, combined with the kit's definition and its Markdown documentation snippets, by
  `clinical_ml_kits.notebooks.build`. **Generated notebooks contain executable Python code for the
  full ML workflow** (explicit scikit-learn baseline construction, `.fit`, prediction, evaluation,
  plots, student models, tuning, comparison). The generator fills code-cell templates with kit
  values; it does not produce configuration wrappers. CI fails if a committed notebook differs from
  its regenerated version (drift check). Cells carry a `ckit_role` tag: `framework` (protected
  infrastructure calls), `baseline` (working example code students can read and modify), or
  `student` (runnable starter code). See [contracts/student-notebook.md](contracts/student-notebook.md).
- **Rationale (vs 7 separate notebooks)**: Colab runtimes don't share state across notebooks,
  so each notebook would re-install, re-load, and re-split data; Colab file storage is
  ephemeral, so passing intermediate files between notebooks is fragile. A single notebook with a
  table of contents and collapsible sections keeps setup to one cell and preserves the
  workflow ordering. Generation guarantees identical structure within a template family (SC-013)
  while keeping the ML code visible; infrastructure is imported, not copied (SC-014).
- **Generated vs hand-written code**: generated cells are written as ordinary, idiomatic code (literal
  parameter values, no indirection), so the result reads like a hand-written teaching notebook.
- **Alternatives**: seven notebooks (repeated setup, ephemeral state); hand-maintained
  notebooks (drift); Jupytext `.py` sources (an extra concept for students; could be used
  internally by the builder later).
- Students save their working copy in Colab (Drive) or in the Workbench workspace; the
  committed notebook stays the clean template.

## R-17 All of Us Workbench data access

- **Decision**: The All of Us adapter reads OMOP CDM tables through the Workbench's documented
  BigQuery access pattern (CDR dataset reference supplied by the Workbench environment), using
  parameterized SQL generated from concept sets and cohort rules, with cutoff and concept filters
  pushed down. The adapter refuses to initialize unless Workbench environment markers are present.
- `VERIFY` (V-10, V-11): current documented access pattern (environment variables, client
  libraries), current CDR version naming, which OMOP tables and fields are populated (e.g.,
  `observation_period`, `visit_occurrence` detail), and Workbench internet access for `pip install`.
- **Rationale**: Filters stay server-side (scale; minimal data in memory); the boundary stays
  thin.
- **Alternatives**: exporting CSVs inside the workspace (extra copies of participant data; no
  benefit).

## R-18 Synthetic data generation

- **Decision**: Two independent synthetic sources, neither derived from All of Us data:
  1. **Golden patients**: hand-authored YAML timelines with expected feature values (tests).
  2. **Synthetic population generator** (one params file per kit, `synthetic/generator_params/<kit_id>.yaml`, including the toy kit): seeded, rule-based generator producing an OMOP-shaped
     person and observation population for notebooks and integration tests. It plants **documented,
     deliberately artificial** relationships so the baseline learns something non-trivial, plus
     controllable missingness and visit patterns. Parameters are invented for software testing,
     labeled "not clinically realistic", and never fitted to real data.
- **Rationale**: Constitution IX and X; FR-098.
- **Alternatives**: Synthea (realistic, independent of AoU; large dependency and outputs; possible
  later for richer demos — would need a license and provenance review); fitting to AoU summaries
  (prohibited derivation risk).

## R-19 Logging and reproducibility

- **Decision**: Standard-library `logging` with a framework logger namespace. A
  `RunManifest` records: framework version and git commit, kit-definition content hash, kit and
  phenotype versions, concept-set versions, feature-registry version, dataset ID and version,
  adapter and environment, seed, split salt, split-manifest digest, library versions, and the
  test-access log. A single `seed` in the kit definition drives NumPy `Generator` and sklearn
  `random_state`.
- **Rationale**: FR-055 and SC-006 without extra infrastructure.
- **Alternatives**: MLflow (infrastructure overhead; may not run in the Workbench).

## R-20 Documentation

- **Decision**: Markdown in the repository. Kit documentation is a fixed set of files per kit
  (see data-model.md "KitDocs"); provenance lives in YAML next to definitions. A static docs site
  (MkDocs) is deferred.
- **Rationale**: GitHub renders Markdown; nothing extra to host.

## R-21 Prediction envelope format and versioning

- **Decision**: The envelope is a Pydantic model serialized to JSON. `contract_version` uses
  semantic versioning (`1.0.0` for M1–4). Additive optional fields bump MINOR; removed or renamed
  fields bump MAJOR. Specialty outputs go in a discriminated `payload` union keyed by
  `payload_type`; M1–4 define only `binary_probability`. Times are ISO-8601 with an
  explicit offset (UTC recommended); horizons are ISO-8601 durations (e.g., `P30D`, `PT12H`).
  See [contracts/prediction-envelope.md](contracts/prediction-envelope.md).
- **Alternatives**: Protocol Buffers or Avro (unnecessary tooling for a course); free-form dicts
  (unvalidated).

## R-22 Deep-learning stack (future specialty kits)

- **Decision**: PyTorch + torchvision is the single primary deep-learning stack, shipped as a `[dl]`
  optional extra when the first deep-learning template is built (M11). Students choose, modify, and
  tune standard architectures (e.g., torchvision models, transfer learning, freezing/unfreezing,
  augmentation, optimizers, learning rates) and never implement backpropagation, gradient descent,
  convolution, or attention from scratch.
- **Rationale**: Widely taught and Colab-preinstalled; torchvision covers 2D imaging and pretrained
  backbones; one framework keeps kits consistent.
- **Alternatives**: TensorFlow/Keras (would split the ecosystem); JAX (less common in coursework).
  Additional specialized libraries (e.g., for 3D medical imaging or signal I/O) are added only with a
  plan justification at M11.

## R-23 Provisional synthetic-only values and validation levels

- **Decision**: Every clinical value is either verified, provisional, or unverified. Provisional
  values are concrete, carry a note and a pending V-ID, and are usable only at the `synthetic`
  validation level. Four levels apply: `schema`, `synthetic`, `workbench`, `approval`. See
  [contracts/kit-definition.md](contracts/kit-definition.md).
- **Rationale**: Reference-kit fixtures and notebooks must run before clinical verification
  completes, without inventing "verified" rules. Making the provisional status explicit and gating
  it by level preserves Constitution XII and FR-158.
- **Alternatives**: block all kit work until verification (stalls M4); silently use placeholder
  values (violates XII).

## R-24 Logical concepts with per-namespace realizations

- **Decision**: Kits, phenotypes, and the registry reference logical concept ids. Each adapter
  resolves them through its namespace (`omop` → verified realizations; `synthetic` → fictional
  `SYN-` codes). Clinical-meaning provenance attaches to the logical concept; mapping provenance
  attaches to each realization.
- **Rationale**: Synthetic mode must not depend on unverified OMOP sets, and kits must not
  depend on one data source (Constitution IV).
- **Alternatives**: per-kit synthetic copies of phenotype rules (duplication); synthetic data
  that reuses real OMOP IDs (implies real mappings).

## R-25 Control sampling and prevalence semantics

- **Decision**: Each phenotype declares `control_sampling` (strategy `all_eligible | random_ratio |
  matched`, controls per case, match attributes, seed, rationale and provenance). There is no
  global default. The sampled development prevalence is recorded; envelopes carry
  `probability_basis: development_sample`; notebooks and limitations docs state that these
  probabilities are not population probabilities.
- **Rationale**: The sampling ratio determines observed prevalence, and with it calibration and
  threshold metrics. Population-level probability claims would need a recalibration method that
  is out of scope for M1–4.

## R-26 Grouped calibration (V-14)

- **Decision**: Whether `CalibratedClassifierCV` passes `groups` to a grouped splitter in the
  scikit-learn versions on Colab (V-13) and the Workbench (V-12) is **verified empirically**
  (V-14), not assumed. If it does not, or does so only through version-specific metadata routing,
  the framework provides `kit.calibrate_grouped(model, method)` (`grouped_oof_*`). A `grouped_native_*` method exists in the schema but is valid only for scikit-learn versions that V-14 verified as safe. It fits a sigmoid or isotonic
  calibrator on out-of-fold predictions from `cross_val_predict(..., cv=kit.cv_splitter(),
  groups=...)` on the training partition, then applies it to a model refit on all training data.
  Validation and test data are never used to fit the calibrator.
- **Rationale**: A silent fallback to ungrouped folds would leak patients across folds in future
  multi-row templates. (M4 kits also satisfy the one-row-per-person invariant.)
