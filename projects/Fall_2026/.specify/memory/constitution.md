<!--
Sync Impact Report
==================
Version change: (unversioned template) → 1.0.0
Bump rationale: Initial ratification; all placeholders replaced with project governance.

Modified principles: N/A (template placeholders [PRINCIPLE_1..5] replaced; principle count
expanded from 5 to 25 per user-supplied mandatory principles).

Added sections:
- Core Principles I–XXV
- Data, Privacy & Clinical Evidence Constraints (was [SECTION_2_NAME])
- Development Workflow & Quality Gates (was [SECTION_3_NAME])
- Governance

Removed sections: none

Templates requiring updates (not modified by this command; they read the constitution at runtime):
- ⚠ .specify/templates/plan-template.md — "Constitution Check" gate should enumerate the
  quality gates in "Development Workflow & Quality Gates" when next reviewed.
- ⚠ .specify/templates/spec-template.md — kit specs should capture prediction type, index time,
  horizon, cohort/target versions, and verification status (Principles VII, XII, XIII).
- ⚠ .specify/templates/tasks-template.md — test tasks MUST precede implementation tasks and
  include the mandatory framework/kit test categories (Principle VIII).

Deferred TODOs: none
-->

# Clinical ML Education Framework Constitution

This framework provides reusable, leakage-safe machine-learning project kits for clinical ML
education, built primarily on the NIH All of Us Research Program with selected specialty datasets.
These principles govern every specification, plan, task, review, and implementation decision.

## Core Principles

### I. Shared Architecture Over Duplicated Code

- The framework MUST be built on a small number of reusable ML templates, not one codebase per kit.
- A kit MUST consist primarily of configuration, clinical documentation, cohort definitions,
  target/label definitions, feature definitions, and dataset-specific mappings. Kit-specific code
  is permitted only when genuinely necessary.
- A new kit MUST reuse an existing template when its ML task is structurally similar.
- If substantial code is copied between kits, the shared architecture MUST be reconsidered.

### II. Core All of Us Strategy

- The core catalog targets approximately 20 clinical/EHR kits using All of Us as the shared
  primary data source.
- Core kits MUST share one clinical data abstraction and mapping layer covering demographics,
  measurements/labs, vital signs, physical measurements, conditions, medications, procedures,
  visits/encounters, surveys, historical data, and wearable/genomic data where appropriate.
- The 20 core kits MUST NOT become 20 independent implementations.

### III. Specialty Kit Quality Over Quantity

- Specialty datasets (e.g., PTB-XL, ISIC Archive, LIDC-IDRI/TCIA, other TCIA collections,
  MedMNIST) MAY be used for modalities poorly represented in All of Us.
- A specialty dataset MAY contribute roughly 1–3 kits; this is not a quota.
- Each specialty kit MUST represent a clinically meaningful, methodologically distinct problem
  with sufficient sample size, appropriate and acceptable-quality labels, a defensible clinical
  question, manageable leakage risk, a meaningful educational objective, and an appropriate baseline.
- A kit that is weak, redundant, clinically vague, poorly labeled, or inadequately supported by its
  dataset MUST NOT be created. A kit MUST NOT be created merely to increase the kit count.

### IV. Dataset Independence

- Dataset-specific code MUST be separated from generic ML code.
- All of Us / OMOP access MUST sit behind a dataset adapter (or equivalent abstraction); other
  datasets MUST use their own adapters where appropriate.
- Generic components — preprocessing, splitting, training, evaluation, calibration,
  explainability, configuration validation, model export, prediction interfaces — MUST NOT depend
  directly on any specific dataset.
- Adding a dataset MUST NOT require rewriting the core ML framework.

### V. Common Student Experience

- Every kit MUST present the same recognizable workflow: understand the clinical problem → load the
  prepared dataset → explore → preprocess → run the baseline → develop an alternative model → tune
  hyperparameters → evaluate → examine calibration where appropriate → explain → select a final
  model → export through the standard interface.
- Differences between kits MUST come only from clinical problem, input modality, target, model
  family, and evaluation requirements — not from incidental differences in organization or tooling.

### VI. ML Validity and Leakage Protection (NON-NEGOTIABLE)

The framework MUST enforce:

- **A. Patient-level splitting** — records from one patient MUST NOT cross train/validation/test.
- **B. Temporal cutoff** — a feature used at prediction time *t* MUST NOT use observations after *t*.
- **C. Target leakage** — features that directly reveal the target MUST be excluded unless
  explicitly justified by the prediction question.
- **D. Label leakage** — information used to construct the outcome MUST NOT become predictor input.
- **E. Preprocessing isolation** — imputers, scalers, encoders, feature selectors, resampling, and
  similar steps MUST be fit on training data only.
- **F. Reproducibility** — random seeds, dataset versions, configuration versions, and model
  settings MUST be controlled where practical.
- **G. Calibration** — models outputting risk/likelihood probabilities MUST have calibration
  evaluated where appropriate.
- **H. Class imbalance** — imbalance MUST be explicitly addressed; AUROC alone is insufficient when
  prevalence is low or other metrics are clinically important.
- **I. Versioned clinical definitions** — cohort, phenotype, outcome definitions, and concept sets
  MUST be explicit and version controlled.
- **J. Explicit missingness** — missing values MUST be handled deliberately and MUST NOT be
  silently treated as normal findings.
- **K. Timeline integrity** — longitudinal features, index times, lookback windows, and future
  outcomes MUST respect patient chronology.

Rationale: silent methodological errors are more serious than ordinary software errors.

### VII. Current State and Future Risk Remain Distinct

- Every kit MUST declare its prediction type as `current_state` (status at the index time, using
  information available up to it) or `future_risk` (probability of a defined outcome after the
  index time).
- Historical information MAY improve a `current_state` model without making it `future_risk`.
- Future-risk capability is NOT required for every kit.
- Prediction horizons MUST be set per kit by the clinical question and dataset (hours, days, months,
  years) and MUST NOT be globally hard-coded.
- Outputs MUST NOT imply that probabilities with different targets or horizons are comparable.

### VIII. Tests Before Scale

- Automated tests MUST be designed alongside or before implementation. Kits MUST NOT be mass-
  produced and validated afterward.
- The shared framework MUST test: patient split integrity, temporal cutoff enforcement, target
  leakage protection, label leakage protection, feature mapping, missing-value behavior,
  preprocessing fit isolation, configuration validation, output schema validation, model
  serialization/deserialization, and reproducibility.
- Every kit MUST support kit-specific tests for cohort construction, target construction, required
  features, excluded features, and prediction-horizon behavior where applicable.

### IX. Synthetic Golden Patients

- Tests MUST use synthetic "golden patient" fixtures with known timelines and expected feature values.
- Fixtures MUST make temporal leakage and extraction failures easy to detect. Example — creatinine
  at 2025-01-01 = 0.9, 2025-06-01 = 1.0, 2026-01-01 = 1.2, 2026-03-01 = 1.5; at index time
  2026-01-01, `latest = 1.2`, `previous = 1.0`, and the 2026-03-01 value MUST NOT appear in any feature.

### X. Real Participant Data Never Enters the Repository (NON-NEGOTIABLE)

- Real All of Us participant-level data or other restricted clinical data MUST NOT be committed to
  source, tests, fixtures, documentation examples, or sample datasets.
- Local development and automated testing MUST use synthetic or otherwise permitted data.
- Restricted data MUST remain within the environment and access controls its dataset requires.

### XI. Educational and Research Use Only

- Code, documentation, and interfaces MUST NOT claim that models are clinically validated, that
  probabilities are approved clinical risk scores, that outputs should guide patient care, or that
  any dashboard is a clinical decision-support system.
- Experimental model outputs MUST be clearly distinguished from validated clinical tools.

### XII. Evidence-Based Clinical Definitions

- All of Us fields, OMOP mappings, lab mappings, diagnosis concept sets, clinical thresholds,
  phenotype definitions, outcome definitions, and prediction horizons MUST NOT be invented.
- Any such value not yet verified MUST be explicitly marked for verification.
- Definitions MUST be supported by official dataset documentation, OMOP documentation, accepted
  clinical guidelines, or peer-reviewed literature.
- Uncertainty MUST be documented rather than silently resolved by assumption.

### XIII. Configuration Over Special-Case Code

- Clinical differences between kits MUST be expressed through configuration whenever practical,
  including: kit ID/name, dataset, template family, clinical question, prediction type, cohort and
  target definitions, index time, lookback, horizon, feature set, exclusion criteria, leakage
  exclusions, baseline model, metrics, calibration, imbalance handling, explainability, output
  metadata, and phenotype version.
- If a kit requires numerous conditional branches in shared code, the team MUST determine whether
  the abstraction is incomplete, a reusable extension point is needed, or the kit belongs to a
  different template family. Kit-specific hacks MUST NOT accumulate.

### XIV. Reusable Baseline Model Templates

- Baselines MUST come from a small set of reusable families, e.g.: binary tabular classification,
  multiclass tabular classification, fixed-horizon longitudinal prediction, survival analysis,
  temporal/wearable modeling, genomic + clinical modeling, image classification, image
  segmentation/detection, and physiological signal classification.
- Baselines MUST be understandable and reproducible, and MUST leave students meaningful room to improve.

### XV. Students Focus on Machine Learning, Not Infrastructure

- The framework MUST provide: raw EHR schema interpretation, OMOP concept resolution, patient-level
  splitting, leakage-safe cohort construction, common preprocessing infrastructure, standardized
  model export, and dashboard integration contracts.
- Student work MUST center on exploratory analysis, feature engineering, alternative model
  selection, hyperparameter optimization, imbalance handling, evaluation, calibration,
  explainability, baseline comparison, and final model selection.

### XVI. Standardized Model Output

- All models MUST expose one shared, versioned prediction interface regardless of implementation.
- The output contract MUST support, where applicable: model identity and version, kit identity,
  target/condition, prediction type, probability or score, optional class label, as-of/index time,
  optional horizon, input/feature metadata, explainability metadata, and model metadata.
- A consumer (e.g., a future dashboard) MUST NOT need knowledge of a model's training internals.

### XVII. Maintainability Over Rapid Generation

- Prefer modularity, configuration-driven behavior, testability, reproducibility, clear and typed
  interfaces where useful, low duplication, deterministic tests, synthetic fixtures, versioned
  schemas, explicit error handling, logging, and maintainable documentation over producing many
  notebooks quickly.
- Notebooks MUST NOT be the only implementation of important shared functionality; such
  functionality MUST live in reusable, tested modules.

### XVIII. Build in Milestones

- Development MUST proceed incrementally. All kits MUST NOT be implemented at once.
- First phase: **M1** repository foundation → **M2** shared clinical/data abstraction → **M3**
  reusable binary tabular baseline template → **M4** three reference All of Us kits: Type 2
  Diabetes, Chronic Kidney Disease, Hypertension.
- An architecture review MUST follow M4. No large-scale kit expansion until the reference kits
  demonstrate: the shared architecture works, duplication is minimal, leakage protections work,
  synthetic tests pass, standardized output works, kit configuration works, and no major
  kit-specific hacks were required.

### XIX. Core Expansion Only After Reference Validation

- Expansion toward ~20 core kits MUST begin only after the reference kits are stable.
- Every added kit MUST meet the same quality requirements.
- A proposed kit MAY be revised, postponed, replaced, or rejected if data, cohort size, clinical
  definition, or labels prove inadequate. Viability MUST NOT be assumed.

### XX. Specialty Datasets Require Their Own Validation

- Specialty kit development MUST begin only after evaluating the actual dataset for: sample size,
  class distribution, patient-level and repeated-patient structure, label provenance,
  current-state vs future-risk suitability, preprocessing requirements, licensing/access
  requirements, leakage risks, and appropriate evaluation strategy.
- Multiple labels within a dataset MUST NOT be assumed to justify multiple kits.

### XXI. Modality-Specific Methods Without Fragmentation

- Different model families per modality are permitted (e.g., tabular/longitudinal for All of Us,
  1D CNNs/signal Transformers for PTB-XL, CNNs/ViTs for ISIC, 3D CNNs/detection/segmentation for
  LIDC-IDRI, simpler classifiers for MedMNIST).
- Evaluation conventions, configuration principles, student workflow, documentation structure, and
  standardized outputs MUST remain as consistent as practical across modalities.

### XXII. Research Correctness Is First-Class

- A model that runs but uses an invalid cohort, leaked feature, inappropriate label, or incorrect
  temporal relationship is incorrect.
- Software correctness, ML methodological correctness, and clinical/research correctness MUST be
  treated and reviewed as separate quality dimensions.

### XXIII. Architectural Review Before Exceptions

- Before adding a special case, the team MUST determine whether the problem reflects a missing
  abstraction, an incorrect abstraction, a new reusable requirement, a dataset-specific
  responsibility, or a truly unique kit need.
- One-off exceptions MUST be rare and documented with justification.

### XXIV. Extensibility Is a Design Requirement

- The architecture MUST allow adding new kits, datasets, model templates, modalities, prediction
  horizons, and dashboard consumers without redesigning the system.
- The initial catalog is not the final boundary of the project.

### XXV. Quality Over Kit Count

- Success is measured by reliable, educationally useful, clinically defensible kits on a
  maintainable shared framework — not by kit count.
- Twenty All of Us kits are the core target; specialty kits are added where supported, and a
  different final count due to legitimate dataset constraints or opportunities is acceptable.
- A clinical question, label definition, evaluation standard, or architecture MUST NEVER be
  weakened to reach a kit-count target.

## Data, Privacy & Clinical Evidence Constraints

- **Data handling**: Restricted data stays in its authorized environment (Principle X). Repository
  CI MUST run entirely on synthetic or permitted data.
- **Verification markers**: Every unverified clinical value (field, concept set, threshold,
  phenotype, horizon) MUST carry an explicit verification marker in configuration and
  documentation, with its intended source noted (Principle XII).
- **Version control of definitions**: Cohort, phenotype, outcome, and concept-set definitions MUST
  carry version identifiers that are recorded in model output metadata (Principles VI-I, XVI).
- **Disclaimers**: Student-facing materials and any output-consuming interface MUST state the
  educational/research-only status of models (Principle XI).

## Development Workflow & Quality Gates

Every specification, plan, and review MUST check the following gates:

1. **Reuse gate** — Does the work reuse an existing template/adapter? If not, is the new
   abstraction justified (I, IV, XIII, XXIII)?
2. **Validity gate** — Are patient-level splitting, temporal cutoff, target/label leakage
   exclusions, preprocessing isolation, missingness handling, and timeline integrity enforced and
   tested (VI)?
3. **Prediction-type gate** — Is `current_state` vs `future_risk` declared, with a kit-specific
   horizon where applicable (VII)?
4. **Test-first gate** — Are framework and kit-specific tests, including golden-patient fixtures,
   written alongside or before the implementation (VIII, IX)?
5. **Evidence gate** — Are clinical definitions sourced or explicitly marked for verification (XII)?
6. **Output gate** — Does the model conform to the standardized, versioned output contract (XVI)?
7. **Data gate** — Is the change free of real participant or restricted data (X)?
8. **Milestone gate** — Is the work permitted by the current milestone (XVIII–XX)?

Reviews MUST assess software, ML methodological, and clinical/research correctness separately (XXII).

## Governance

- This constitution supersedes all other project practices. Where guidance conflicts, the
  constitution prevails.
- **Amendments** MUST be proposed in writing with rationale, reviewed by project maintainers, and
  recorded in the Sync Impact Report at the top of this file, including any migration impact on
  existing kits and templates.
- **Versioning** follows semantic versioning: MAJOR for removing or redefining a principle in a
  backward-incompatible way; MINOR for adding a principle/section or materially expanding guidance;
  PATCH for clarifications and wording fixes.
- **Compliance**: Every plan's Constitution Check and every review MUST verify the quality gates
  above. Deviations MUST be documented with justification (Principle XXIII) or the work MUST be revised.
- The architecture review after Milestone 4 is a mandatory governance checkpoint; its findings MAY
  trigger constitution amendments.

**Version**: 1.0.0 | **Ratified**: 2026-10-15 | **Last Amended**: 2026-10-15
