# Implementation Plan: Clinical ML Kit Framework

**Branch**: `001-clinical-ml-kit-framework` | **Date**: 2026-10-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-clinical-ml-kit-framework/spec.md`

**Scope of detail**: The full system is planned architecturally. Detailed technical design covers
**Milestones 1–4 only**. Milestones 5–11 get direction only (§ 19).

Companion artifacts: [research.md](research.md) (decisions R-01…R-21),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md).

## Summary

One installable Python package (`clinical_ml_kits`) holds all shared, tested **infrastructure**
(adapters, OMOP mapping, cohort/label and feature construction, splitting, leakage checks,
reusable preprocessing and evaluation helpers, envelope and provenance validation, completion).
Each kit contains its YAML definition, phenotype definition, versioned concept sets with inline
provenance, Markdown docs, kit-specific tests, and a generated **executable Jupyter notebook**
whose Python code shows the full ML workflow: loading, EDA, an explicit scikit-learn baseline
pipeline that is fitted and evaluated, student models, tuning, comparison, calibration,
explainability, and completion ([contracts/student-notebook.md](contracts/student-notebook.md)).
The rule is **no duplicated framework infrastructure in kits**, not "no Python in kits". The
notebook switches between a synthetic adapter (Colab, CI) and an All of Us Workbench adapter
behind one adapter protocol. Leakage protection is enforced structurally (cutoff views,
train-only pipelines, hidden test partition, concept-set intersection checks) and verified with
synthetic golden patients. The Workbench policy is encoded as a `DataEnvironmentPolicy`, so
research models never leave the Workbench and the framework never relies on model export.

## 1. Technical Context

**Language/Version**: Python ≥ 3.10 (CI: 3.10 and the current Colab default) — R-01

**Primary Dependencies**: pandas, numpy, scikit-learn, pydantic v2, PyYAML, matplotlib, joblib
(via sklearn); `[aou]` extra: the Workbench's documented BigQuery client (V-10); future `[dl]`
extra: PyTorch + torchvision (M11 only) — R-02, R-05, R-22

**Storage**: Files in the repo (YAML definitions, Markdown, generated notebooks); no database.
Real data stays in the Workbench (BigQuery CDR; workspace storage for completion records).

**Testing**: pytest, nbmake, golden-patient fixtures, mock AoU query backend — R-07

**Target Platform**: Google Colab and standard Jupyter (synthetic/public); All of Us Researcher
Workbench Jupyter (real data); GitHub Actions CI

**Project Type**: Python library + generated notebooks + declarative kit definitions (+ a small
CLI, `ckit`, for validation and notebook generation)

**Performance Goals**: Synthetic kit notebook runs end to end in Colab in < 5 min on the free
tier. Workbench feature extraction scales to cohorts of the order of 10⁵ persons and 10⁷
observation rows through server-side filtering and vectorized pandas (no per-patient loops).

**Constraints**: No participant-level data or derived synthetic data outside the Workbench; no
dependency on model export; compatibility with preinstalled Colab and Workbench libraries; no
invented clinical definitions (sentinel `UNVERIFIED`).

**Scale/Scope**: M1–4: 1 template family, 2 adapters, 3 kits. Long term: ~20 core kits, ≤ ~3 kits
per specialty dataset, ~9–11 template families.

No `NEEDS CLARIFICATION` items remain. External facts that need confirming are tracked as
verification tasks (§ 21) and do not block design.

## 2. Constitution Check

*Gate evaluated before Phase 0 and re-checked after Phase 1 design: **PASS** (no violations; Complexity Tracking is empty).*

| Gate | Design element(s) satisfying it | How M1–4 prove it |
|---|---|---|
| 1 Reuse (I, IV, XIII, XXIII) | Single package for infrastructure; kits = definitions + docs + generated executable notebook; notebooks import shared helpers instead of re-implementing them; adapter protocol; RuleExpr predicates instead of kit-specific infrastructure code | Post-M4 review: 3 kits, zero kit-specific code under `src/`; notebook content checks find no re-implemented infrastructure; add-a-kit dry run (quickstart § 5); import-boundary test |
| 2 ML validity (VI) | Hash patient split; CutoffView + TemporalPolicy + lineage check; concept-set intersection; sklearn Pipeline fitted on train only; hidden test partition; typed `Missing` | `tests/leakage/*` with golden patients and broken fixtures (SC-005); split-integrity test on every kit |
| 3 Prediction type (VII) | `prediction_type` required; horizon iff `future_risk` (schema + envelope rules) | Schema tests; all 3 kits validate as `current_state` with null horizon |
| 4 Test-first (VIII, IX) | Each milestone lists its tests first; contract suites for adapters and envelope; golden fixtures | CI green is the milestone exit criterion; tests are committed before or with the code |
| 5 Clinical evidence (XII, FR-150–158) | SourceRecords; inline ProvenanceRefs; value states **verified / provisional (synthetic-only, labeled, pending V-ID) / unverified (`UNVERIFIED`)**; four validation levels (`schema`, `synthetic`, `workbench`, `approval`); P-1…P-11 (P-10 provisional note and V-ID, P-11 single source for the verification log); status gating. Provisional values support synthetic execution only, never Workbench execution or `approved` status; approval requires verified evidence and FR-081 evidence | `ckit validate` blocks `approved`; each kit's verification_log enumerates open items |
| 6 Standard output (XVI) | Prediction envelope v1.0.0 with a discriminated payload | Envelope contract tests; all 3 kits emit valid envelopes |
| 7 Data/privacy (X, XI) | DataEnvironmentPolicy; AoU adapter refuses outside the Workbench; independent synthetic generator; dissemination filter per V-03; repo data guard; disclaimer constant | Data-guard CI job; quickstart § 4 refusal checks; no participant data in the repo (SC-007) |
| 8 Milestone (XVIII–XX) | Only Template A and 3 kits are built; specialty work is interface-only; mandatory post-M4 stop gate (§ 18) | Review record committed before any M5 work |

## 3. Recommended Architecture

```text
 Student notebook (.ipynb, generated)      ← narrative, EDA, student cells
        │  kit = load_kit("aou_t2d_current", data_source=...)
        ▼
 Kit definition (YAML) + phenotype + concept sets + docs   ← data, validated
        ▼
 Template API  (templates/binary_tabular)  ← fit / evaluate / final_evaluation / predict / complete
        ▼
 Shared framework logic
   cohort/  features/  temporal/  leakage/  splitting/  preprocessing/
   evaluation/  prediction/  provenance/  completion/  core/
        ▼
 Data adapter protocol (data/adapter.py)
        ├── adapters/synthetic_clinical   (golden fixtures, seeded generator; Colab/CI)
        └── adapters/all_of_us            (Workbench only; OMOP over BigQuery)
            (future: ptbxl, isic, tcia, medmnist via SampleAdapter)
```

**Dependency rule**: arrows only point down. `adapters/*` import `data/` types only; nothing
imports `adapters/*` except the registry. Templates never touch adapters directly.

**Alternative considered**: a separate pipeline per kit (fast for 3 kits, but violates I and XIII
at 20+ kits); a plugin-per-kit Python class hierarchy (puts clinical logic in code; violates FR-155).
Rejected.

## 4. Major Interfaces

| Interface | Location | Contract |
|---|---|---|
| `load_kit(kit_id, data_source)` → `Kit` | `clinical_ml_kits/__init__` | Validates the definition, binds the adapter and policy, builds the RunManifest |
| `Kit.load()` → `KitData` | `core/kit.py` | Cohort → labels → index times → split → features; test partition hidden |
| `Kit.patient(id).as_of(t)` → `CutoffView` | `features/` | [patient-feature-api.md](contracts/patient-feature-api.md) |
| `DatasetAdapter` / `DataEnvironmentPolicy` | `data/adapter.py` | [dataset-adapter.md](contracts/dataset-adapter.md) |
| Template A helpers: `make_preprocessor`, `kit.cv_splitter`, `evaluate_binary`, `plot_roc_pr`, `plot_calibration`, `coefficient_table`, `compare_models` | `preprocessing/`, `splitting/`, `evaluation/` | § 16 below; called from visible notebook code |
| Student notebook | `kits/<dataset>/<kit>/kit.ipynb` (generated) | [student-notebook.md](contracts/student-notebook.md) |
| `kit.final_evaluation(model)` | `evaluation/` | Single logged test evaluation (R-11) |
| `kit.to_envelopes(model, X)` | `prediction/` | [prediction-envelope.md](contracts/prediction-envelope.md) |
| `completion.complete(model)` / `completion.save_model(model, portable=…)` | `completion/` | Policy-gated (R-14, R-15) |
| `ckit validate \| notebooks \| catalog` | `cli.py` | Validation and generation entry points |

## 5. Configuration and Schema Design

- **Format**: YAML + Pydantic v2 + generated JSON Schema (R-03). The full field table and
  cross-field rules are in [contracts/kit-definition.md](contracts/kit-definition.md).
- **Schemas versioned independently**: `kit_schema` 1.0, envelope `contract_version` 1.0.0,
  registry and concept-set versions (semver), phenotype versions.
- **Clinical differences live in YAML**: cohort and control rules (RuleExpr), temporal policy
  (same-day, washout, index encounter, windowed exclusions), features and derivations,
  prohibited items, thresholds, metrics, calibration, split.
- **Value states and validation levels** (R-23): every clinical value is verified, provisional
  (concrete, synthetic-only, with a note and a pending V-ID), or unverified (`UNVERIFIED`
  sentinel). Levels: `schema` (CI), `synthetic` (no sentinels in executed values; provisional
  allowed), `workbench` (no provisional or unverified required values; verified `omop`
  realizations), `approval`. This separates synthetic executability from Workbench and clinical
  approval validity. Provisional values never reach the Workbench or approval and are bannered in
  docs and notebooks.
- **Control sampling** (R-25): declared per phenotype; no global default; prevalence semantics
  recorded.
- **Split salt** fixed and versioned per kit; changes require a version bump and a reason (R-10).

## 6. Dataset-Adapter Design

See [contracts/dataset-adapter.md](contracts/dataset-adapter.md). Key points:
- A minimal protocol (`metadata`, `policy`, `persons`, `observations`, `visits`,
  `index_candidates`). History and cohort logic are generic, not per adapter.
- `observations(before=…)` is an exclusive upper bound that every adapter must honor. The
  shared contract suite runs against every adapter (synthetic and mocked AoU).
- AoU adapter: Workbench-only initialization, parameterized SQL from verified `omop` realizations (built in M4 after V-10/V-11), pushdown
  filters, unit normalization via the registry, no disk writes.
- Specialty adapters later implement `SampleAdapter`; same split routine on `patient_key`.

## 7. Patient / Feature Abstraction

See [contracts/patient-feature-api.md](contracts/patient-feature-api.md) and data-model § 1.
- `CutoffView` (per patient, for teaching) and `FeatureMatrixBuilder` (vectorized, for
  training) share one derivation library; golden tests assert identical results.
- Every value carries value, canonical unit, time, domain, concept, source table, and mapping
  version. Missingness is a typed `Missing(reason)`.
- Derivations: latest, previous, delta, pct_change, mean, rolling_mean(window), min, max, std,
  slope, count, time_since_last — all computed on cutoff-filtered data only.
- **Feature registry** (`definitions/features/registry.yaml`) maps semantic keys to **logical
  concepts** (R-24). Each adapter resolves logical concepts through its namespace: `omop`
  realizations (verified only; members empty until verified, P-5) for All of Us, and fictional
  `SYN-` realizations for synthetic mode. No concept IDs are created during planning. The AoU
  adapter raises `PendingVerification` for any unverified realization.
- **Grouping**: every partition carries an opaque `groups` key in all modes; current-state
  binary kits satisfy the one-row-per-person invariant (data-model § 4).

## 8. Provenance / Documentation Design

See [contracts/provenance.md](contracts/provenance.md) and data-model §§ 2, 6.
- SourceRecords (`definitions/sources/`) carry the 1–6 priority tier. ProvenanceRefs sit inline
  beside each item. Verified items are content-hashed, so a silent edit reverts them to
  `requires_verification`.
- Statuses: `draft → requires_verification → verified → approved` (kits). Approval is impossible
  while any required item is unverified (P-4).
- KitDocs: README (reviewer Q&A index, FR-156), clinical_background, construction (follows the
  FR-154 sequence), features (included/excluded + mapping table), limitations, verification_log
  (generated). Notebook Markdown is pulled from these files, so each fact is written once.

## 9. Prediction-Output Design

See [contracts/prediction-envelope.md](contracts/prediction-envelope.md). v1.0.0: required identity,
type, as-of, dataset, definition versions, environment, subject ref, disclaimer; `horizon` null for
`current_state`; payload `binary_probability` for M1–4; reserved slots for multiclass, survival,
segmentation, detection, and signal.

## 10. Notebook Strategy

Full contract: [contracts/student-notebook.md](contracts/student-notebook.md).

- **One generated, executable `kit.ipynb` per kit + `00_setup_check.ipynb`** (R-16). Sections:
  0 Setup · 1 Clinical problem · 2 Dataset and cohort · 3 EDA · 4 Preprocessing · 5 Baseline model ·
  6 Evaluate the baseline · 7 Your model · 8 Hyperparameter tuning · 9 Model comparison ·
  10 Calibration · 11 Explainability · 12 Final selection and completion. These cover all 12
  workflow steps of FR-040.
- **Visible Python ML workflow**: cells contain real code for imports, `load_kit`, data inspection,
  pandas/matplotlib EDA, `make_preprocessor(...)`, an explicit
  `Pipeline([... LogisticRegression(...)])`, `.fit`, `.predict_proba`, `evaluate_binary`, plots,
  starter student models (RandomForest, HistGradientBoosting/GradientBoosting, SVC, KNN), and
  `GridSearchCV` with patient-grouped folds (`kit.cv_splitter()`), comparison, calibration,
  permutation importance, `final_evaluation`, and completion.
- **The baseline runs end to end** with no student edits. Student work starts after the working
  baseline (§§ 7–12).
- **Standard libraries only**: scikit-learn for traditional ML; PyTorch + torchvision for future
  deep-learning kits. Students never implement algorithms or model internals from scratch.
- **Cell roles** (`ckit_role` tag): `framework` (setup, loading, leakage checks, final evaluation,
  completion; banner "do not edit"; restorable; hash recorded), `baseline` (working example code;
  readable and modifiable, but students copy it into their own cells to keep the comparison point),
  `student` (runnable starter code). Expected outputs are described in Markdown before each code cell.
- **Generation renders code, not wrappers**: template-family cell templates (stdlib
  `string.Template`) are filled with values from `kit.yaml` (feature lists, baseline parameters,
  threshold rule, metrics). The generated baseline cell therefore reads
  `LogisticRegression(C=1.0, ...)` literally, and a test asserts it matches `kit.yaml`.
- No Colab-only APIs: installation uses `%pip`; Drive mounting is optional and offered only in
  Markdown instructions.
- Drift control: CI regenerates notebooks and fails on differences; outputs are stripped.
- Integrity: the setup cell records the framework version and kit-definition hash in the
  RunManifest; the completion record includes them, so edits to protected infrastructure are
  detectable.

## 11. Repository Structure

**Structure decision**: the framework lives in `projects/Fall_2026/` of the existing
`UNF-AIRO-Club` repository (single Python project).

```text
projects/Fall_2026/
├── pyproject.toml · uv.lock · README.md · .pre-commit-config.yaml
├── src/clinical_ml_kits/
│   ├── __init__.py            # load_kit
│   ├── cli.py                 # ckit validate | notebooks | catalog
│   ├── core/                  # kit_schema (pydantic), kit.py, environment, run_manifest, logging, errors, seeds
│   ├── data/                  # adapter protocol, policy, observation schema, adapter registry
│   ├── adapters/
│   │   ├── synthetic_clinical/  # fixtures loader, population generator
│   │   └── all_of_us/           # Workbench-only; sql builder; [aou] extra
│   ├── cohort/                # RuleExpr evaluator, phenotype/label construction, index rules
│   ├── temporal/              # TemporalPolicy, effective cutoff, CutoffView
│   ├── features/              # registry loader, derivations, FeatureMatrixBuilder, patient view
│   ├── splitting/             # hash split, split manifest, test-partition guard
│   ├── leakage/               # patient/temporal/target/label/preprocessing/same-day checks
│   ├── preprocessing/         # Template A ColumnTransformer factory
│   ├── templates/binary_tabular/
│   ├── evaluation/            # metrics, threshold rules, calibration, explainability, plots
│   ├── prediction/            # envelope models, to_envelope
│   ├── provenance/            # source/provenance models, P-1..P-11 checks, hashing
│   ├── completion/            # completion record, policy-gated save, V-03 dissemination filter
│   └── notebooks/             # builder + per-template notebook templates (.ipynb skeletons)
├── definitions/
│   ├── sources/               # SourceRecord YAML
│   ├── features/registry.yaml
│   ├── concepts/<logical_id>.yaml            # logical concepts (clinical-meaning provenance)
│   └── concept_sets/{omop,synthetic}/<logical_id>/<version>.yaml   # realizations (mapping provenance)
├── kits/
│   ├── catalog.yaml           # 25 candidates + statuses + rationale
│   └── all_of_us/
│       ├── type_2_diabetes/       # kit.yaml, phenotype.yaml, verification.yaml, evidence/fr081.yaml, docs/ (verification_log.md generated), tests/, kit.ipynb (generated)
│       ├── chronic_kidney_disease/
│       └── hypertension/
├── synthetic/
│   ├── golden/                # hand-authored patient timelines + expected values
│   └── generator_params/      # <kit_id>.yaml per kit (incl. toy): artificial, not clinically realistic, participant-independent
├── tests/
│   ├── unit/ · contract/ · leakage/ · integration/ · notebooks/ · repo/ (data guard, import boundaries)
├── docs/                      # architecture, conventions, schemas/ (generated JSON Schema), review records
└── (repo root) .github/workflows/clinical-ml-kits.yml
```

Where things belong: source code → `src/`; kit configs → `kits/<dataset>/<kit>/kit.yaml`;
phenotypes → beside the kit; logical concepts → `definitions/concepts/`; realizations → `definitions/concept_sets/<namespace>/`; verification notes → `kits/.../verification.yaml`; FR-081 evidence → `kits/.../evidence/`; notebooks → generated into
each kit folder; provenance → inline plus `definitions/sources/`; synthetic fixtures →
`synthetic/`; framework tests → `tests/`; kit tests → `kits/.../tests/`.

## 12. Testing Strategy

Tests are written with or before each module (constitution VIII). Layout and coverage:

| Suite | Covers |
|---|---|
| `tests/unit/core` | Kit-schema validation (every cross-field rule, value states, validation levels schema/synthetic/workbench/approval, control sampling, salt versioning), run manifest, seeds |
| `tests/unit/docs` | Generated verification log equals `ckit docs` output; `verification.yaml` has no status fields; README answers all 12 FR-156 questions with resolving links |
| `tests/contract/adapter` | Shared adapter contract (exclusive `before`, schema columns, units) × each adapter (synthetic, mocked AoU) |
| `tests/contract/envelope` | Envelope rules 1–4, JSON round-trip, JSON Schema generation |
| `tests/unit/provenance` | P-1…P-11, content-hash reversion, status gating |
| `tests/leakage/split` | No person in >1 partition; repeated measurements stay together; hash stability when the cohort grows |
| `tests/leakage/groups_cv` | `groups` present in all modes, shared within a person, distinct across persons, never in `X` or outputs; grouped CV receives groups (synthetic and mocked AoU); one-row-per-person invariant; V-14 grouped-calibration behavior |
| `tests/leakage/temporal` | Golden creatinine example (both entry points); lineage check catches a planted post-index row |
| `tests/leakage/same_day` | `exclude_index_day`, washout, index-encounter exclusion, windowed exclusions, date-only precision |
| `tests/leakage/target_label` | Prohibited and label-defining intersection fails; justified inclusion passes; features unaffected by label-function changes |
| `tests/leakage/preprocessing` | Imputer/scaler statistics equal train-only statistics; a fit on validation/test rows is detected |
| `tests/unit/features` | Each derivation, missing reasons, unit rejection, plausible-range flags, registry mapping |
| `tests/unit/missingness` | NaN never becomes a "normal" value; indicators present; `min_features_present` rule |
| `tests/unit/completion` | Policy matrix (portable refused in AoU), dissemination filter exactly per V-03 (synthetic counts; blocked while V-03 unresolved), no writes into the git checkout |
| `tests/integration` | Synthetic end to end for each reference kit; reproducibility (same manifest → identical metrics) |
| `tests/notebooks` | nbmake runs every kit notebook end to end with no edits; structure check (sections, `ckit_role` tags); content checks (baseline builds and fits a standard estimator; no SQL, raw file reads, or split code in cells; no placeholders in framework/baseline cells; baseline parameters match `kit.yaml`); drift check |
| `tests/repo` | Data guard (blocks large CSV/parquet files and files with person-ID-like columns outside `synthetic/`); import-boundary rules |
| `kits/*/tests` | Cohort rules, positive labels, controls, index time, required features, prohibited features, verification status (expects `requires_verification` until approved) |

## 13. Technology Recommendations

| Concern | Choice | Ref |
|---|---|---|
| Packaging/deps | pyproject + hatchling; `uv` for maintainers; `pip` from a git tag for students | R-02 |
| Config validation | Pydantic v2 + YAML; generated JSON Schema | R-03 |
| Data | pandas (long-format observations) | R-04 |
| ML baseline + student models | scikit-learn (LR baseline; RF, gradient boosting, SVC, KNN as starters) | R-05 |
| Deep learning (future) | PyTorch + torchvision, single DL stack | R-22 |
| Calibration/explainability | sklearn calibration utilities, coefficients, permutation importance | R-05, R-06 |
| Testing | pytest, nbmake | R-07 |
| Notebook generation/hygiene | nbformat builder rendering executable cell templates (stdlib `string.Template`), nbstripout | R-07, R-16 |
| Lint/format/types | ruff, mypy, pre-commit | R-08 |
| CI | GitHub Actions | R-09 |
| Serialization | joblib + JSON sidecar, policy-gated | R-14 |
| Logging/repro | stdlib logging, RunManifest | R-19 |
| Docs | Markdown; MkDocs deferred | R-20 |

## 14. Milestone 1 — Repository Foundation (detailed)

**Goal**: A working, testable skeleton with every schema and guard in place before any clinical
logic.

| Area | Deliverable |
|---|---|
| Repo/package | Structure in § 11; `pyproject.toml` (runtime deps, `[aou]` and `[dev]` extras); `uv.lock`; `ckit` entry point |
| Config schema | Pydantic `KitDefinition`, `TemporalPolicy`, `CohortDefinition`, `PhenotypeDefinition` (incl. `ControlSampling`), `RuleExpr` over logical concepts; value states (verified, provisional synthetic-only, `UNVERIFIED`); validation levels `schema`/`synthetic`/`workbench`/`approval`; split salt versioning; `synthetic_population`; calibration method rules (`grouped_native_*` gated on V-14); JSON Schema export |
| Provenance schema | SourceRecord, ProvenanceRef, Deviation; P-1…P-11 checks; content hashing; status machine |
| Prediction schema | Envelope v1.0.0 + `binary_probability` payload; JSON Schema export |
| Test framework | pytest config; markers (`unit`, `contract`, `leakage`, `notebook`, `workbench`, the last skipped by default) |
| Synthetic fixture framework | Golden-patient YAML format + loader + expected-value assertions; first fixtures (creatinine timeline, same-day cases, control with sparse history, multi-visit patient) |
| Logging | Framework logger namespace; consistent error classes (`KitValidationError`, `LeakageError`, `ProhibitedFeatureError`, `EnvironmentNotPermitted`, `PolicyViolation`) |
| Reproducibility | Seed plumbing; RunManifest model; library-version capture |
| Notebook conventions | Template skeleton format, cell tags, banner text, section list; builder stub that renders headings |
| Doc conventions | KitDocs file set + templates; `docs/conventions.md`; source-tier guidance |
| Catalog | `kits/catalog.yaml` with the 25 candidates (`candidate` status; 3 reference kits flagged) |
| CI + guards | Workflow (lint → types → tests → validate → notebooks → data guard); pre-commit; data-guard test |

**Tests first**: schema validation cases (valid/invalid fixtures for every rule), envelope rules,
provenance checks, data guard.
**Exit criteria**: CI green; `ckit validate` runs on a stub kit; invalid kit fixtures produce named
errors; the data guard blocks a planted `persons.csv`.

## 15. Milestone 2 — Shared Clinical Data Abstraction (detailed)

| Area | Deliverable |
|---|---|
| Adapter protocol | `DatasetAdapter` (incl. `resolve(logical_concept)` and `metadata().namespace`), `DataEnvironmentPolicy` (with required validation level per environment), adapter registry, observation/person schemas |
| Logical concepts and realizations | `definitions/concepts/<logical_id>.yaml` (clinical-meaning provenance) and `definitions/concept_sets/<namespace>/<logical_id>/<semver>.yaml` realizations (mapping provenance); `omop` members empty until verified (P-5); fictional `SYN-` synthetic namespace clearly marked as not real OMOP; kits reference logical ids only (data-model § 2) |
| Synthetic adapter | Namespace `synthetic`. **Golden backend** for deterministic unit and edge tests; **population backend** (seeded generator driven by per-kit `synthetic/generator_params/<kit_id>.yaml`, artificial header, not clinically realistic, independent of participant data) for end-to-end model and notebook execution; pandas pushdown filters |
| AoU adapter boundary | Namespace `omop`; Workbench guard; protocol methods raise `PendingVerification`; **no SQL or queries in M2** (implemented in M4 after V-10/V-11, § 17) |
| Patient representation | `PatientTimeline`, `CutoffView`, typed `Obs`/`Missing` |
| Feature registry | `registry.yaml` with semantic keys for the FR-031 categories referencing logical concepts; units and plausible ranges verified or provisional/`UNVERIFIED` pending V-25; no OMOP IDs |
| Historical feature API | Derivation library shared by the patient view and `FeatureMatrixBuilder`; lineage output |
| Provenance tracking | `mapping_version` (realization version) stamped on observations; traceability check P-8 (feature → logical concept → realization → source) |
| Temporal cutoff | `TemporalPolicy` → effective-cutoff function; mandatory explicit same-day choice (verified, provisional, or `UNVERIFIED`) |
| Cohort and control sampling | RuleExpr evaluator over logical concepts; case/control/index construction separate from feature construction; `control_sampling` (all_eligible / random_ratio / matched, seeded); sampled development prevalence recorded |
| One-row-per-person invariant | Enforced in `kit.load()` for `binary_tabular` + `current_state` kits (all M4 reference kits) |
| Splitting and groups | Hash split with fixed, versioned salt; split manifest; per-partition minimum-positives check; hidden-test guard; opaque `groups` key on every partition in **every** execution mode (masked, never a feature, never in outputs) |
| Grouped cross-validation | `kit.cv_splitter()` grouped splitter used with `groups=`; V-14 empirical verification of `CalibratedClassifierCV` group propagation; `kit.calibrate_grouped` OOF helper (`grouped_native_*` only if V-14 verifies it) |
| Leakage infrastructure | Checks for patient, temporal (lineage), target/label (logical-concept intersection), same-day/windowed, plus preprocessing hooks used in M3 |

**Tests first**: adapter contract suite (incl. namespace resolution: synthetic never resolves `omop`,
AoU never resolves `synthetic`); logical-concept/realization validation (P-5, P-8); golden-patient
derivations (both entry points); same-day matrix; control-sampling reproducibility and one row per
person; split integrity, stability, and salt versioning; `groups` present in synthetic and mocked
AoU modes, shared within a person, distinct across persons, absent from `X` and outputs; grouped
CV folds never split a group; V-14 result recorded before the calibration helper; generator
params header enforcement and population sufficiency; leakage intersection checks; AoU boundary
stub raises `PendingVerification` (no SQL).
**Exit criteria**: all M2 tests green; the synthetic adapter produces a cohort and feature matrix for the
toy kit from its generator population; no generic module imports `adapters/*` (boundary test).

## 16. Milestone 3 — Binary Tabular Template (Template A, detailed)

Template A = (1) a notebook skeleton with executable cell templates, (2) shared helpers the
notebook calls, and (3) baseline defaults declared in `kit.yaml`. The baseline pipeline is
**assembled and fitted in visible notebook code**; helpers supply only reusable infrastructure.

**Baseline pipeline** (visible in notebook §§ 4–5; preprocessing from the shared
`make_preprocessor(feature_spec)`, fitted only on `data.train`):
- Numeric: `SimpleImputer(strategy="median", add_indicator=True)` → `StandardScaler`.
- Categorical: `SimpleImputer(strategy="constant", fill_value="__missing__")` →
  `OneHotEncoder(handle_unknown="ignore")`.
- Rows failing the kit's `min_features_present` rule are excluded **before** splitting, by a
  declared rule, with counts logged.
- Model: `LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=…, class_weight=None)`
  by default. Unweighted training keeps probabilities calibrated to the training prevalence.
  Imbalance is addressed through metrics (AUPRC) and threshold selection on validation; class
  weighting and resampling are student explorations, and any resampling must happen inside the
  training fold only.

**Training and evaluation flow (notebook code + shared helpers)**:
- Visible: `baseline = Pipeline([("preprocess", make_preprocessor(kit.feature_spec)),
  ("model", LogisticRegression(...))])`; `baseline.fit(data.train.X, data.train.y)`;
  `baseline.predict_proba(data.validation.X)`.
- Helpers: `evaluate_binary(y, proba, threshold_rule)`, `plot_roc_pr`, `plot_calibration`,
  `coefficient_table`, `compare_models`, `kit.cv_splitter()` (patient-grouped `GroupKFold` within
  train, used with `groups=data.train.groups` in every execution mode, so tuning can't leak
  patients across folds), `kit.calibrate_grouped(model, method)` (if required by V-14; R-26),
  `kit.final_evaluation(model)` (test, once, logged), `kit.to_envelopes(model, X)`,
  `kit.complete(model)`.
- Unsafe model selection is rejected by the notebook content rules: any search, CV, or
  `CalibratedClassifierCV` call without `cv=kit.cv_splitter()` and groups
  (contracts/student-notebook.md).
- Student models: any scikit-learn-compatible estimator, preferably in a `Pipeline` with the shared
  preprocessor. `final_evaluation` runs a preprocessing-isolation check on Pipelines (fitted
  statistics must match training-only statistics) and warns for non-Pipeline objects.
- Starter alternatives shown in the notebook: `RandomForestClassifier`,
  `HistGradientBoostingClassifier`/`GradientBoostingClassifier`, `SVC(probability=True)`,
  `KNeighborsClassifier`.

**Evaluation**: AUROC, AUPRC (reported with prevalence as the baseline), sensitivity, specificity,
precision, recall, F1, and the confusion matrix at the declared `threshold_rule` (selected on
validation and reused on test); bootstrap CIs on test. **Calibration**: reliability curve
(quantile bins), Brier score, calibration intercept and slope. Calibration is assessed relative
to the **sampled development prevalence**. When `control_sampling.strategy ≠ all_eligible`,
probabilities are not population disease probabilities; envelopes carry
`probability_basis: development_sample`, and the notebook and limitations docs say so prominently.
**Explainability**: standardized coefficients (including missingness indicators) and permutation
importance on validation; per-prediction contributions in the envelope.
**Output**: envelope v1.0.0 with `binary_probability` payload and `calibration_status`.
**Completion/serialization**: `completion.complete()` always works and produces a
CompletionRecord (in AoU, aggregates are filtered per the V-03 rule; blocked until V-03 is
resolved). `save_model(portable=True)` works only when the policy allows it.
**Notebook integration**: the Template A executable notebook skeleton (sections 0–12, cell
templates with real code) is finalized; the builder renders it with kit values and docs.

**Tests first**: preprocessing isolation; threshold chosen on validation only; metric correctness on
fixed toy data; calibration math; grouped CV splitter (no patient in two folds); envelope validity;
policy matrix; reproducibility (same seed → identical coefficients and metrics); a toy synthetic kit
notebook runs end to end under nbmake with no edits; notebook content checks (baseline cell
constructs and fits an estimator; no re-implemented infrastructure; rendered baseline parameters
match `kit.yaml`).
**Exit criteria**: a toy kit completes in a synthetic Colab run in < 5 min; all template tests green.

## 17. Milestone 4 — Reference Kits (detailed)

Common to all three kits: `template_family: binary_tabular`; `prediction_type: current_state`;
task = "given information that does not define the phenotype, does the patient currently meet the
validated phenotype?" (FR-130). Positive = the record is consistent with the phenotype at the index
time (not a diagnosis). Case index = date the phenotype is first established. Control index = one
eligible visit per control person, chosen under the kit's declared `control_sampling`. Controls
require observation history and **positive control evidence** (FR-132). Earlier label-defining
values are prohibited (FR-134). **One modeled row per person** (enforced at load). Phenotype,
concept, and sampling choices reference **logical concepts**; synthetic runs use `SYN-`
realizations and may use **provisional** values (labeled, synthetic-only) where verification is
incomplete, so the kits can be built and tested before approval. Workbench runs and approval
require verified values.
**Every clinical item below is a verification question, not a definition.**

### Shared M4 verification questions (all kits)
- Control index sampling: how to avoid **index-visit bias** (cases are indexed at diagnostic
  encounters rich in labs; random control visits are not). Options to evaluate: match controls on
  visit type and calendar year; exclude utilization-count features at the index encounter.
- Same-day policy, washout, index-encounter exclusion (FR-137) per kit.
- Minimum observation history and lookback; whether observation periods exist in AoU (V-11).
- Control sampling per kit (strategy, controls per case, matching attributes, seed) and its effect
  on sampled prevalence, calibration, and threshold metrics; documented distinction from
  population prevalence.
- FR-081 data-availability evidence (eligible persons, positives, controls, class balance,
  feature availability, missingness and coverage, longitudinal coverage) captured inside the
  Workbench, with only V-03-permitted aggregates recorded outside it.

### 17.1 Type 2 Diabetes (`aou_t2d_current`)
- **Clinical question**: Does the record (excluding glycemic and diabetes-specific evidence) indicate
  the patient currently meets a validated T2D phenotype?
- **Phenotype items to verify**: case rule (combinations of diagnosis codes, HbA1c/glucose
  criteria, diabetes medications); T1D and other diabetes types excluded; repeat-evidence needs;
  whether gestational diabetes is handled; source candidates: a validated EHR T2D phenotype
  algorithm (e.g., eMERGE/PheKB-type), ADA Standards of Care diagnostic criteria (tier 4), All of
  Us and OMOP docs.
- **Control items to verify**: required negative evidence (e.g., a documented non-diabetic
  glycemic test within a window — used only for label construction, never as a feature);
  exclusion of prediabetes or not; minimum history.
- **Index/same-day**: case index = first date the case rule is met; whether index-day labs
  (lipids, metabolic panel ordered with the HbA1c) are excluded.
- **Candidate feature categories**: demographics (age; sex if justified), BMI, weight, BP, lipids,
  renal panel, liver panel, hematology, utilization history, selected comorbidity history.
- **Prohibited (initial; finalize from the verified phenotype)**: diabetes diagnoses, HbA1c, glucose,
  diabetes medications; **review for indirect revealers**: diabetic complication codes (retinopathy,
  neuropathy, nephropathy), glucose-monitoring supplies and procedures, diabetes education visits,
  endocrinology referrals.
- **Concept sets needed**: t2d_diagnosis, t1d_and_other_diabetes (exclusion), hba1c, glucose,
  diabetes_medications, plus each feature's measurement set.

### 17.2 Chronic Kidney Disease (`aou_ckd_current`)
- **Clinical question**: Does the record (excluding kidney-function and kidney-diagnosis evidence)
  indicate the patient currently meets a validated CKD phenotype?
- **Phenotype items to verify**: eGFR- and/or albuminuria-based criteria with chronicity
  (persistence over a duration, e.g., per KDIGO — tier 4), diagnosis-code criteria, eGFR equation
  and version (e.g., race-free CKD-EPI 2021) and whether eGFR is computed or taken from the source;
  repeat requirements; AKI exclusion; dialysis and transplant handling.
- **Control items to verify**: required normal kidney-function evidence on ≥ N occasions; minimum
  history.
- **Index/same-day**: index = date chronicity is satisfied (the second qualifying measurement?) —
  to verify; same-day labs excluded or not.
- **Candidate feature categories**: demographics, BP, BMI, glucose-independent metabolic data
  (lipids), hematology (anemia is a CKD correlate; allowed unless the phenotype uses it), liver,
  electrolytes, comorbidity and utilization history.
- **Prohibited (initial)**: CKD diagnoses, creatinine, eGFR, urine albumin/protein; **review**: BUN,
  cystatin C, dialysis/transplant procedures, nephrology visits, kidney-specific medications, and
  potassium/bicarbonate if the phenotype or its workup uses them.
- **Concept sets needed**: ckd_diagnosis, creatinine, egfr, urine_albumin_protein, dialysis_transplant,
  aki_diagnosis (exclusion), plus feature sets.

### 17.3 Hypertension (`aou_htn_current`)
- **Clinical question**: Does the record (excluding BP measurements, HTN diagnoses, and
  phenotype-defining antihypertensives) indicate the patient currently meets a validated HTN phenotype?
- **Phenotype items to verify**: BP threshold and number of readings or visits (guideline choice,
  e.g., ACC/AHA vs other — tier 4), diagnosis codes, medication criteria; handling of
  antihypertensives with other indications (beta-blockers for AF, ACE inhibitors/ARBs for HF or
  diabetic kidney disease); secondary/pregnancy hypertension.
- **Control items to verify**: required normal BP readings on ≥ N visits without antihypertensives;
  minimum history.
- **Index/same-day**: index = date the criteria are first met; whether same-visit vitals (heart rate)
  are allowed.
- **Candidate feature categories**: demographics, BMI and weight, heart rate (review), lipids, glucose
  and HbA1c (allowed here), renal and liver panels, hematology, comorbidity and utilization history.
- **Prohibited (initial)**: HTN diagnoses, BP measurements, antihypertensives that are part of the
  phenotype; **review**: hypertensive heart/kidney disease codes, home BP monitoring.
- **Concept sets needed**: htn_diagnosis, systolic_bp, diastolic_bp, antihypertensive_medications
  (by class), secondary_htn and pregnancy (exclusion), plus feature sets.

### All of Us adapter implementation (M4, after V-10/V-11)
- SQL builder for verified `omop` realizations, parameterized (no string-interpolated values),
  with concept, person, and `before` filters pushed down, using only tables and fields marked
  populated in V-11 and the V-10 access pattern.
- **Tests first**: against a mock query backend returning synthetic OMOP-shaped rows: the SQL
  contains concept, time, and person filters; the parameterization is correct; and
  `test_adapter_contract.py` passes for the mocked AoU adapter. Live verification is the manual
  Workbench checklist (quickstart § 4).

### Per-kit deliverables (all three)
- `kit.yaml`, `phenotype.yaml` (status `requires_verification`), concept-set files (members empty until
  verified), SourceRecords for the cited sources, KitDocs (six files), the generated `kit.ipynb`.
- **Kit tests**: cohort rules on golden patients (a case meeting the rule; a near-miss non-case; a
  control with positive evidence; a "no diagnosis but no evidence" patient who is **not** a control);
  index time correctness; required features present; prohibited and label-defining features absent
  (intersection check); same-day policy applied; the status check fails if marked approved while
  unverified.
- **Notebook content**: background (why the task matters; why it is phenotype inference rather
  than threshold reproduction), construction narrative, excluded-feature explanation, a missingness EDA
  prompt, baseline, student sections, and a limitations section.

### M4 acceptance criteria
1. All three kits validate and run end to end in synthetic mode (Colab and CI).
2. All three use Template A with zero kit-specific code under `src/`. Each kit notebook runs a
   complete baseline end to end with visible scikit-learn code and no student edits.
3. All kit and framework tests are green.
4. Envelopes are valid; completion behaves per policy.
5. Provenance is complete for every item that has been researched; every other item is listed as
   `UNVERIFIED / REQUIRES REVIEW`.
6. Workbench verification run (quickstart § 4) completed **once the definitions are verified**.
   Kits move to `approved` only after verification and reviewer sign-off. A kit may finish M4 as
   `requires_verification`, and that is reported, not hidden.

## 18. Post-Milestone-4 Architecture Review (mandatory stop gate)

Recorded as `docs/reviews/post-m4-review.md`. **Milestone 5 cannot start until every item passes or
the architecture is revised and re-reviewed.**

1. All three kits use the same Template A implementation.
2. No major framework logic is duplicated (notebooks or kits).
3. Kit differences are configuration and definitions only.
4. AoU-specific code exists only under `adapters/all_of_us/` (import-boundary test).
5. No patient crosses partitions (split tests on all kits).
6. Preprocessing is fit on train only (isolation tests).
7. Temporal restrictions work (golden and lineage tests).
8. Same-day and workup rules work (same-day matrix + per-kit policy tests).
9. Target-defining features are excluded (intersection tests).
10. Golden-patient suites pass.
11. Provenance is complete (P-1…P-11 clean).
12. Clinical definitions are verified before any approval (P-4).
13. Envelopes conform to v1.0.0.
14. Synthetic mode runs in Colab (nbmake + manual Colab smoke run).
15. All three kits run end to end (synthetic; Workbench where verified).
16. Add-a-kit dry run requires no `src/` change; only kit-specific artifacts change (kit and phenotype YAML, logical concepts and realizations, synthetic population settings, docs, tests, regenerated notebook) (quickstart § 5).
Also record: friction points, abstractions to adjust, and whether RuleExpr predicates sufficed.

## 19. Milestones 5–11 (direction only)

- **M5 Remaining approved AoU binary kits**: candidates go through FR-081 evaluation in the Workbench
  (aggregate evidence filtered per V-03); approved ones are added as YAML + docs; candidates that need
  multiclass, longitudinal, or survival templates wait for M6–M8. New RuleExpr predicates go
  through review, not kit code.
- **M6 Multiclass template** (e.g., Anemia Phenotype/Type): multinomial LR; envelope
  `multiclass_probability` (MINOR bump); per-class calibration and metrics.
- **M7 Longitudinal/future-risk template**: outcome windows after the index; horizon in kit and
  envelope; landmark-style index sampling; censoring and loss to follow-up rules; candidates for
  onset/progression extensions of the reference kits.
- **M8 Survival template**: Cox PH baseline (dependency choice deferred); `survival` payload
  design; time-dependent evaluation (C-index, time-specific calibration).
- **M9 Wearable/temporal**: Fitbit-type summaries via the AoU adapter (domain to verify); engineered
  temporal summaries + traditional ML.
- **M10 Genomic + clinical**: derived genomic features only (e.g., risk scores) under Controlled
  Tier rules; elastic-net LR; dimensionality handling; additional policy review.
- **M11 Specialty datasets and dashboard**: `SampleAdapter` implementations after the FR-082
  evaluation of each dataset; 1D-signal, 2D/3D-image, segmentation, and detection templates (likely
  PyTorch + torchvision as the single deep-learning stack, in a `[dl]` extra; any additional
  specialized library, e.g. for 3D medical imaging, needs a plan justification); payload definitions; cross-kit validation;
  dashboard consuming demo-model envelopes only.

## 20. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Incorrect phenotype definitions | Invalid labels | Tier-ranked sources; verification status gating; reviewer sign-off; deviations recorded |
| Incorrect OMOP mappings | Wrong features/labels | Concept sets empty until verified; P-5/P-8; unit acceptance lists; Workbench aggregate sanity checks (distribution by unit) |
| Target leakage | Inflated metrics | Prohibited lists + label-defining intersection; review list of indirect revealers per kit |
| Same-day diagnostic leakage | Inflated metrics | Mandatory explicit TemporalPolicy; index-encounter and windowed exclusions; same-day tests |
| Temporal leakage | Invalid model | CutoffView by construction; adapter `before`; lineage check |
| Patient leakage | Optimistic test results | Hash split on person; split tests; specialty grouping key |
| Preprocessing leakage | Optimistic results | Pipeline fit on train only; isolation tests; warnings for non-Pipeline student models |
| Poor control definitions | Label noise, spurious signal | Positive control evidence required; "no-evidence" patients excluded; verification |
| Index-visit bias | Model learns visit context | Control index matching options; review of utilization features; documented in limitations |
| Missingness (informative) | Bias, "missing = normal" | Typed Missing; indicators; EDA prompts; `min_features_present` |
| Class imbalance | Misleading AUROC | AUPRC required; threshold on validation; prevalence reported |
| Dataset/site heterogeneity | Poor generalization; unit inconsistency | Unit normalization and rejection logging; limitations docs; subgroup EDA (filtered per V-03) |
| AoU policy constraints | Non-compliance | DataEnvironmentPolicy; Workbench-only adapter; V-03 dissemination filter; no derived synthetic data; V-01–V-04 |
| Workbench runtime constraints | Install/run failures | Python ≥ 3.10; minimal deps; `00_setup_check`; V-12 |
| Model portability restrictions | Dashboard can't use AoU models | Demo models on synthetic data; architecture never depends on export |
| Colab compatibility | Student friction | CI on the Colab Python version; no Colab-only APIs; < 5 min synthetic run |
| Notebook drift | Inconsistent kits | Generated notebooks + CI drift check |
| Infrastructure creeping into notebooks | Duplication, untested code | Helper boundary rule (student-notebook contract); notebook content checks; SC-014 review. ML workflow code stays visible by design |
| Notebooks reduced to opaque wrappers | Students can't see or modify the ML workflow | Contract requires visible estimator construction, `.fit`, and evaluation code; content checks fail if missing |
| Duplicated kit logic | Maintenance burden | Kit-specific *infrastructure* lives only in shared modules; notebooks are generated from one skeleton; RuleExpr extension through review |
| Students asked to implement algorithms | Wrong learning focus | Standard estimators only (scikit-learn; PyTorch/torchvision later); contract rule 3 |
| Configuration drift | Kits diverge from schema | Versioned kit schema; `ckit validate` in CI; migration notes on schema bumps |
| Provenance drift | Stale "verified" status | Content hashes revert edited items (P-7) |
| Students modifying protected infrastructure | Invalid results | Pinned package tag; framework-tagged cells restorable; manifest hash in completion record |
| Weak labels | Low learning value | FR-081 label-quality check; reject or postpone candidates |
| Baselines near chance | Little learning value | Expected and acceptable once leakage is removed; report against prevalence; reviewed at the post-M4 gate (may prompt a revised feature set, not leakage) |
| Research probabilities mistaken for clinical risk scores | Misuse | Disclaimer constant in envelopes and notebooks; dashboard labeling; constitution XI |
| Synthetic data mistaken for realistic | False conclusions | Generator labeled "not clinically realistic"; notebook banner in synthetic mode |
| Provisional values mistaken for official definitions | Invalid clinical claims | Explicit value state with note and pending V-ID; banner in docs and notebooks; blocked from Workbench and approval (P-4, P-10) |
| Sampled prevalence read as population risk | Misleading probabilities | `probability_basis: development_sample` in envelopes; notebook calibration Markdown; limitations requirement in the kit schema |
| Group key exposure | Pseudonymous participant-derived values leave the Workbench | Masked repr; excluded from `X`, envelopes, and records; policy refuses writes; tests |

## 21. Remaining Verification Tasks

| ID | Item | Source to consult | Blocks |
|---|---|---|---|
| V-01 | Model-download/export rule for models trained on participant data (official text) | All of Us support / Policy Questions page / DUCC | Nothing (architecture assumes no export); documentation |
| V-02 | Whether models trained only on dissemination-compliant summary data may leave | All of Us support | Later demo strategy |
| V-03 | Small-count dissemination threshold and scope: Workbench-internal vs leaving it; confusion matrices, calibration bins, subgroup tables, descriptive stats, derived metrics; public-repository content (README stats, notebook outputs, figures, CI artifacts) | Data & Statistics Dissemination Policy; All of Us support | Workbench completion records, FR-081 evidence export (M3/M4) |
| V-14 | Whether `CalibratedClassifierCV` propagates `groups` to grouped splitters in the Colab and Workbench scikit-learn versions | Empirical test against the V-12/V-13 versions; scikit-learn docs | Grouped calibration helper (M2/M3) |
| V-04 | Whether the Workbench can host or serve models | All of Us support | Nothing in M1–4 |
| V-10 | Workbench data-access pattern (environment variables, client libraries), CDR version naming | Workbench docs | AoU adapter live run (M4) |
| V-11 | Populated OMOP tables and fields in the current CDR (observation_period, visit detail, units) | AoU data browser and docs | Cohort/temporal rules (M4) |
| V-12 | Workbench Python and preinstalled package versions; pip/internet access | Workbench docs | Packaging (M1) |
| V-13 | Current Colab Python and library versions | Colab | CI matrix (M1) |
| V-20 | Same-day, washout, and index-encounter policies per kit | Phenotype literature + methodological review | Kit approval (M4) |
| V-21 | T2D phenotype, controls, repeat evidence, concept sets | Validated EHR phenotype algorithm(s), ADA Standards, OMOP vocab | T2D approval |
| V-22 | CKD phenotype (chronicity, eGFR equation, albuminuria), controls, concept sets | KDIGO, validated EHR CKD phenotypes, OMOP vocab | CKD approval |
| V-23 | HTN phenotype (BP criteria and readings, medications), controls, concept sets | ACC/AHA (or chosen) guideline, validated EHR HTN phenotypes, OMOP vocab | HTN approval |
| V-24 | Indirect label-revealer review lists per kit | Clinical review | Kit approval |
| V-25 | Unit and plausible-range definitions for registry features | OMOP/UCUM docs, lab references | Feature registry `verified` |

## 22. Decisions Intentionally Deferred

- Detailed specialty payloads (survival, segmentation, detection, signal) and the `SampleAdapter`
  design → M8/M11.
- Survival library choice → M8. (Deep-learning framework is decided: PyTorch + torchvision;
  only additional specialized libraries are deferred to M11 with justification.)
- Wearable and genomic architecture details → M9/M10.
- Dashboard UI, hosting, and demo-model distribution format (e.g., skops) → M11.
- Phenotype definitions for kits beyond the three reference kits → M5+.
- Static documentation site → when docs volume warrants it.
- Polars or other performance backends → only if the Workbench scale requires it.
- Whether to add Synthea-based richer synthetic demos → after the post-M4 review.

## Complexity Tracking

No constitution violations. Table intentionally empty.
