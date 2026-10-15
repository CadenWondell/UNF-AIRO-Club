# Feature Specification: Clinical ML Kit Framework

**Feature Branch**: `001-clinical-ml-kit-framework`

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "Specify the full Clinical ML Kit Framework (complete long-term scope, not limited to Milestone 1): ~20 core All of Us kits from a 25-candidate pool, extensible specialty catalog (PTB-XL, ISIC, LIDC-IDRI/TCIA, other TCIA, MedMNIST) with ~1–3 kits per dataset only where justified, no fixed kit count."

## Overview

A reusable, semester-long clinical machine-learning education framework. Students receive
structured clinical ML **project kits** — each with a clinically meaningful prediction problem,
a prepared dataset, predefined cohort and target, starter features, a working baseline, and
standardized output requirements — so they spend the semester on machine learning rather than on
data access, EHR schemas, or infrastructure.

**Scope**: This specification covers the complete intended system: approximately 20 core
clinical/EHR kits built on the NIH All of Us Research Program, an extensible specialty-kit catalog
(PTB-XL, ISIC Archive, LIDC-IDRI/TCIA, other TCIA collections, MedMNIST, and future datasets), a
shared prediction contract, and a future research/education dashboard. There is no fixed total kit
count. Delivery is phased per the constitution (Principle XVIII): implementation will initially be
limited to Milestones 1–4, but this specification defines the full long-term scope so that later
milestones do not require redefining the project.

**Not a clinical tool**: The framework, its kits, and its dashboard are educational and research
proof-of-concept systems. Nothing in this specification describes clinically validated risk
scores, approved clinical decision support, diagnostic conclusions, or treatment recommendations.

### Actors

- **Student** — receives a kit and carries out the ML project.
- **Instructor / Kit Author** — defines, documents, and maintains kits.
- **Kit Reviewer** — evaluates candidate kits and datasets for approval (clinical, methodological,
  and educational quality). May be the same person as the instructor.
- **Framework Maintainer** — maintains shared templates, dataset adapters, validity protections,
  and the prediction contract.
- **Dashboard Consumer** — any downstream viewer (initially the future dashboard) that displays
  model outputs without knowledge of model internals.

## Clarifications

### Session 2026-10-15

- Q: How should the three reference kits (T2D, CKD, Hypertension) define their baseline prediction
  task without reproducing the label's own threshold? → A: Option A — current-state
  phenotype-inference tasks: "given the patient's available non-target-defining clinical
  information, estimate whether the patient currently meets the validated disease phenotype."
  Phenotype-defining information is excluded from model input entirely, including earlier values
  of target-defining measurements; exclusions derive from the verified phenotype definitions,
  not a hard-coded list. See FR-130–FR-137.
- Q: Should the survey-based success criteria (old SC-013 student time on modeling, old SC-014
  perceived workflow consistency) stay or move? → A: Option B — removed. No student survey or
  education-evaluation milestone is required. Replaced by objective framework criteria SC-013–SC-015
  (identical notebook structure per template family, no duplicated framework logic in notebooks,
  no infrastructure work in student areas); SC-003 already covers configuration-driven kit addition.
- Q: Should Milestone 4 reference kits include future-risk prediction? → A: No (user direction) —
  `current_state` only, using pre-index history; future onset/progression models are later,
  separate kits/extensions on the longitudinal template (FR-130, FR-134).
- Q: Can models trained on All of Us participant-level data be exported? → A: No; research models
  stay in the Workbench. Deliverables split into research model / portable project definition /
  demo model as the initial architecture (FR-095–FR-099). Synthetic data must be generated
  independently of participant data (FR-098).
- Q: How are notebooks delivered and run? → A: Standard .ipynb, Colab preferred where data rules
  allow; one portable notebook per kit with a switchable synthetic/public vs Workbench adapter;
  no participant data in Colab (FR-140–FR-144).
- Q: How is work divided between notebooks and shared code? → A: Hybrid structure is a formal
  requirement: notebooks for narrative, EDA, and student work; tested shared modules for all
  framework logic; no duplication (FR-145–FR-147).
- Q: What does "export" mean? → A: Replaced by distinct terms — model serialization, model
  completion, portable project definition, prediction interface, demo model (see terminology above
  FR-095).
- Q: What is the minimum prediction-contract envelope for Milestones 1–4? → A: Defined in FR-094
  with mandatory, conditional, and optional fields and an extensible specialty payload slot.
- Q: Which lower-impact items are deferred? → A: Specialty payloads, survival output, wearable and
  genomic architecture, specialty adapters, dashboard UI, later-kit phenotypes (Open Item 12).
- Q: How must kit definitions be sourced and documented? → A: Documentation-first with explicit
  provenance for every kit (All of Us and specialty): six-level source hierarchy, provenance
  records on definitions and mappings, feature → concept set → domain → documentation
  traceability, declarative inspectable definitions, recorded deviations, and no approval while
  required definitions are `UNVERIFIED / REQUIRES REVIEW` (FR-150–FR-158).
- Q: How can reference kits run in synthetic mode before clinical verification finishes, without
  inventing verified rules? → A: Provisional values: concrete, explicitly labeled synthetic-only
  values with a note and a pending verification ID. They are allowed for synthetic execution and
  tests only, never for Workbench execution or approval, and never presented as official
  definitions. Kits reference logical concepts resolved per data source (fictional synthetic codes
  vs verified OMOP realizations). FR-071 and FR-158 are unchanged: an item with a provisional value
  is still unverified for approval purposes. (Planning correction from analysis; see plan § 5.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Student completes a project using a kit (Priority: P1)

A student receives one kit (e.g., Chronic Kidney Disease). They read the clinical background and
clinical question, understand exactly what the target means, load the prepared cohort through the
standard loading mechanism, explore the data and its missingness, run the provided baseline and see
its evaluation, build at least one alternative model, tune it, address imbalance and calibration
where appropriate, explain it, select and justify a final model, and complete it through the
standardized prediction interface (FR-095).

**Why this priority**: This is the core value of the framework. Every other capability exists to
make this journey possible, consistent, and methodologically valid.

**Independent Test**: Give a single reference kit, running on permitted (synthetic or authorized)
data, to a student with no prior exposure to the underlying data schema; they can run the baseline
end-to-end and complete a model conforming to the prediction contract without writing data-mapping,
splitting, or leakage-prevention code.

**Acceptance Scenarios**:

1. **Given** a kit, **When** a student opens it, **Then** they find the project title, clinical
   question, clinical background, why the problem matters, dataset description, cohort definition,
   inclusion/exclusion criteria, target definition, starter features, and known limitations.
2. **Given** a kit, **When** the student loads data through the standard mechanism, **Then** they
   receive predefined patient-level train/validation/test partitions (or an equivalent safe
   splitting mechanism) and cannot accidentally receive the same patient in more than one partition.
3. **Given** a kit, **When** the student runs the baseline, **Then** it completes and produces the
   kit's declared evaluation metrics, including imbalance-appropriate metrics and calibration
   results where the kit requires them.
4. **Given** a student-developed model, **When** the student completes it, **Then** its outputs
   conform to the standardized prediction contract or are rejected with a message stating which
   requirement is unmet; for All of Us kits the trained model remains inside the Researcher
   Workbench (FR-095).
7. **Given** an All of Us kit notebook, **When** it runs in synthetic mode in Google Colab or
   another standard Jupyter environment, **Then** it executes end-to-end without Workbench access;
   **When** the same notebook runs with the Workbench adapter inside the Researcher Workbench,
   **Then** it executes on real data without any change to the notebook's analysis steps.
5. **Given** two kits with different modalities (e.g., a tabular EHR kit and an ECG kit), **When**
   a student compares them, **Then** both follow the same recognizable 12-step workflow (FR-040).
6. **Given** a longitudinal kit, **When** the student reads it, **Then** it states the index time,
   lookback window, prediction horizon, outcome definition, and temporal leakage protections.

---

### User Story 2 - Kit author adds a new All of Us kit by reuse (Priority: P1)

An instructor wants to add a new core kit (e.g., Hypertension after Type 2 Diabetes exists). They
declare the kit's clinical question, cohort, target, features, prohibited features, prediction
type, and evaluation expectations, select an existing baseline-template family, and reuse the
shared All of Us data abstraction. They do not write a new pipeline.

**Why this priority**: Reuse is what makes ~20 core kits feasible and maintainable. If kits cannot
be added this way, the architecture has failed (Constitution I, XIII).

**Independent Test**: After one reference kit exists, a second structurally similar kit can be
added consisting only of declarative kit definition, clinical documentation, and kit-specific
tests, with no changes to shared components.

**Acceptance Scenarios**:

1. **Given** an existing binary tabular template, **When** an author defines a new binary tabular
   kit, **Then** the kit runs end-to-end using only its declarative definition, documentation, and
   kit-specific tests.
2. **Given** an incomplete or inconsistent kit definition (e.g., a `future_risk` kit with no
   horizon, or a feature listed as both required and prohibited), **When** the kit is validated,
   **Then** validation fails with a message naming the problem.
3. **Given** a kit definition referencing a clinical value (concept set, threshold, horizon) not
   yet verified, **When** the kit is validated or documented, **Then** that value is visibly
   marked `UNVERIFIED / REQUIRES REVIEW` (FR-071), and the kit cannot be approved (FR-158).
4. **Given** a new kit that appears to need kit-specific logic in shared components, **When** the
   author proposes it, **Then** the framework requires a documented architectural decision
   (missing abstraction, new extension point, different template family, or justified exception)
   before the change is accepted.

---

### User Story 3 - Reviewer approves or rejects a candidate kit (Priority: P2)

A reviewer evaluates a candidate (e.g., "Sleep Apnea" from the All of Us pool, or "ISIC malignancy
classification") against the data-availability and approval criteria, and records a decision:
retain, revise, merge, postpone, replace, or reject.

**Why this priority**: Quality over kit count (Constitution III, XIX, XX, XXV) depends on an
explicit, recorded gate before any candidate becomes a kit.

**Independent Test**: A candidate can be taken through the approval checklist and produce a
recorded decision with supporting evidence, independent of whether the kit is ever built.

**Acceptance Scenarios**:

1. **Given** a candidate with insufficient positive cases, **When** reviewed, **Then** the decision
   record shows the failing criterion and the candidate is not approved.
2. **Given** a specialty dataset with multiple labels, **When** a reviewer proposes multiple kits
   from it, **Then** each proposed kit must independently justify a distinct clinical question,
   target, modeling problem, and educational objective; label count alone is not accepted.
3. **Given** two candidates that duplicate each other's prediction question, **When** reviewed,
   **Then** one is merged, rejected, or justified by a documented educational reason.
4. **Given** the approved core catalog, **When** it contains fewer than 20 kits because candidates
   failed review, **Then** this is an acceptable outcome and no weak candidate is added to fill the gap.

---

### User Story 4 - Validity protections catch methodological errors (Priority: P2)

A maintainer or author introduces a change that would leak information — a feature computed from
observations after the index time, a feature that reveals the target, a scaler fit on the full
dataset, or a patient appearing in both train and test. The framework detects and reports it
before the kit is used.

**Why this priority**: A model that runs but is methodologically invalid is incorrect
(Constitution VI, XXII). Silent errors are worse than failures.

**Independent Test**: Using synthetic golden-patient fixtures with known timelines, each class of
leakage can be deliberately introduced and is detected.

**Acceptance Scenarios**:

1. **Given** a golden patient with creatinine 0.9 (2025-01-01), 1.0 (2025-06-01), 1.2 (2026-01-01),
   1.5 (2026-03-01) and index time 2026-01-01, **When** features are derived, **Then** latest = 1.2,
   previous = 1.0, and the 2026-03-01 value appears in no feature.
2. **Given** a patient with records in multiple partitions, **When** partitions are validated,
   **Then** validation fails.
3. **Given** a feature on the kit's prohibited/leakage list, **When** it is included as input,
   **Then** validation fails unless an explicit justification is recorded.
4. **Given** preprocessing fit on non-training data, **When** the pipeline is validated, **Then**
   it fails.
5. **Given** a patient missing a lab value, **When** features are derived, **Then** the value is
   represented as missing (not silently filled with a "normal" value) and handled per the kit's
   declared missingness strategy.

---

### User Story 5 - Onboarding a specialty dataset and modality (Priority: P3)

A maintainer adds a specialty dataset (e.g., PTB-XL ECG). After the dataset passes specialty
evaluation, they add a dataset adapter and, if needed, a new baseline-template family (e.g.,
physiological signal classification). The resulting kit uses the same workflow, kit definition
semantics, evaluation conventions, documentation structure, and prediction contract as All of Us
kits.

**Why this priority**: Specialty modalities broaden the educational range but depend on the shared
framework being proven first (Constitution XVIII–XXI).

**Independent Test**: A specialty kit can be added without modifying generic components
(splitting, evaluation, calibration, explainability, configuration validation, model serialization, prediction
interface) and its output is consumable by the same dashboard consumer as an All of Us kit.

**Acceptance Scenarios**:

1. **Given** a new dataset, **When** it is onboarded, **Then** dataset-specific logic is confined
   to its adapter and generic components are unchanged.
2. **Given** a dataset where one patient contributes multiple samples (e.g., several lesion images),
   **When** splits are produced, **Then** splitting is by patient, not by sample.
3. **Given** a specialty kit, **When** its model is completed, **Then** its outputs conform to the
   same prediction contract as All of Us kits.

---

### User Story 6 - Dashboard presents current assessments and future risks (Priority: P3)

A dashboard consumer displays, for a synthetic or otherwise permitted patient record and using only
demo models trained on permitted data (FR-097), current-state assessments
from multiple kits based on the most recently available data, and — where kits provide them —
future-risk estimates labeled with their specific outcome and horizon.

**Why this priority**: The dashboard is a downstream consumer; it depends on the prediction
contract but is not required for students to complete projects.

**Independent Test**: Outputs from at least three kits of different template families can be
displayed by one consumer that has no model-specific logic.

**Acceptance Scenarios**:

1. **Given** outputs from several kits, **When** displayed, **Then** each shows its target,
   prediction type (current state vs future risk), as-of time, and horizon where applicable.
2. **Given** a 30-day readmission risk and a 5-year mortality risk, **When** displayed together,
   **Then** they are not presented on a shared scale, ranked against each other, or otherwise
   implied to be comparable.
3. **Given** any displayed output, **When** a user views it, **Then** an educational/research-only
   disclaimer is visible.

---

### Edge Cases

- **Sparse longitudinal coverage**: A patient has no measurements within the lookback window — the
  framework must represent this explicitly (missing / zero count / time-since-last undefined) rather
  than dropping or imputing silently; kit inclusion criteria decide whether the patient is eligible.
- **Measurements on the index date**: Observations timestamped exactly at the index time — the
  framework must apply one documented, consistent rule for inclusion (at-or-before the index time is
  allowed per Constitution VI-B) and must handle date-only vs datetime precision consistently.
- **Outcome defined by a predictor**: A diagnosis code or lab threshold used to define the target
  also appears as a candidate feature — it must be on the kit's prohibited list (label leakage).
- **Very low prevalence**: Positive cases are rare — kits must declare imbalance-appropriate
  metrics; AUROC alone is insufficient; candidates with too few positives fail approval.
- **Repeated patients in specialty datasets**: Multiple images/signals per patient — splits must
  group by patient; if patient identity is unavailable, the reviewer must document the leakage risk
  and decide whether the kit is viable.
- **Dataset version change**: The source dataset releases a new version — outputs and evaluations
  must record which version they used; results across versions are not silently mixed.
- **Unverified clinical value**: A threshold or concept set has no verified source — it remains
  explicitly marked and is reported in kit documentation; it is never silently treated as final.
- **Sex-specific or demographic-restricted targets**: A clinical question applies only to a
  subpopulation — the cohort definition must express this; demographic variables are used only
  where appropriate for the clinical question.
- **Multiclass and multi-output kits** (e.g., Anemia Phenotype/Type): The contract must carry
  per-class probabilities, not only a single score.
- **Segmentation/detection outputs** (e.g., LIDC-IDRI): Outputs that are not a single probability
  must still carry contract identity, prediction type, as-of time, and model metadata.
- **Kit without future-risk capability**: Requests for future risk from a current-state-only kit
  must not produce a value.
- **Restricted data in a contribution**: Any attempt to add participant-level restricted data to
  the repository must be blocked or flagged before acceptance.

## Requirements *(mandatory)*

### Functional Requirements

#### Kit contents (what students receive)

- **FR-001**: Every kit MUST provide: project title, clinical question, clinical background, why the
  problem matters, dataset description, cohort/sample definition, inclusion criteria, exclusion
  criteria, target definition, starter input features, a standardized data-loading mechanism,
  predefined patient-level train/validation/test partitions or an equivalent safe splitting
  mechanism, baseline preprocessing, a working baseline model, baseline evaluation, evaluation
  utilities, standardized output requirements, model completion requirements (FR-095), and
  documented known limitations.
- **FR-002**: Every longitudinal kit MUST additionally provide: index-time definition, lookback
  definition, prediction horizon, outcome definition, and a description of its temporal leakage
  protections.
- **FR-003**: Kits MUST NOT require students to perform raw All of Us/OMOP mapping, build
  patient-level splitting infrastructure, build leakage-prevention infrastructure, build dataset
  adapters, implement dashboard integration protocols, or implement model serialization or
  prediction-interface protocols.
- **FR-004**: Kits MUST leave students responsible for and give them room to perform: exploratory
  analysis, target and feature understanding, missingness analysis, feature selection and
  engineering, alternative model development, hyperparameter tuning, imbalance strategies,
  calibration evaluation, baseline comparison, explainability, final model selection and
  justification, and model completion through the standardized prediction interface.

#### Kit definition (declarative)

- **FR-010**: Each kit MUST be described declaratively with at least: kit ID, kit name, dataset,
  dataset version, clinical question, clinical description, prediction type, baseline-template
  family, cohort definition, inclusion criteria, exclusion criteria, target definition,
  phenotype/outcome definition version, input features, prohibited features, known leakage risks,
  index time (where applicable), lookback window (where applicable), prediction horizon (where
  applicable), baseline model family, evaluation metrics, class-imbalance expectations, calibration
  expectations, explainability expectations, output requirements, and known limitations. The
  specific definition format is not fixed by this specification.
- **FR-011**: The framework MUST validate kit definitions and reject incomplete or internally
  inconsistent definitions with a message identifying the problem.
- **FR-012**: Clinical differences between kits MUST be expressible through the kit definition
  whenever practical; kit-specific logic in shared components MUST require a documented
  architectural decision.
- **FR-013**: A kit MUST be able to extend shared behavior only through declared extension points,
  and any kit-specific extension MUST be documented with its justification.

#### Prediction types and horizons

- **FR-020**: Every kit MUST declare its prediction type(s): `current_state` and/or `future_risk`.
- **FR-021**: A `current_state` prediction MUST use only information available at or before the
  index time; it MAY use historical information (prior values, trends, diagnoses, medications,
  encounters) without being classified as `future_risk`.
- **FR-022**: A `future_risk` prediction MUST specify a defined outcome occurring after the index
  time and a kit-specific horizon.
- **FR-023**: Horizons MUST be defined per kit (any unit from hours to years) and MUST NOT be
  globally fixed.
- **FR-024**: Future-risk capability MUST be optional per kit and included only when the dataset
  and label definition justify it; a kit MAY provide both a current-state assessment and one or
  more future-risk estimates (e.g., current CKD assessment plus progression risk).
- **FR-025**: No output, document, or display MUST present predictions for different targets or
  different horizons as directly comparable.

#### Core All of Us data abstraction

- **FR-030**: All of Us data access MUST be provided through one shared patient-data abstraction
  reused by all core kits, isolated from generic ML components behind a dataset adapter.
- **FR-031**: The abstraction MUST be capable of exposing, where supported by the actual data:
  demographics (age; sex where appropriate; other validated variables); vitals and physical
  measurements (systolic/diastolic BP, heart rate, respiratory rate, BMI, height, weight);
  metabolic (glucose, HbA1c); renal (creatinine, eGFR, BUN); lipids (LDL, HDL, triglycerides, total
  cholesterol); hematology (hemoglobin, hematocrit, RBC, WBC, platelets, MCV, RDW); liver (AST, ALT,
  alkaline phosphatase, bilirubin, albumin); electrolytes (sodium, potassium, calcium,
  bicarbonate/CO2); thyroid (TSH, free T4 where available); clinical history (conditions,
  medication exposures, procedures, hospital and emergency encounters, prior utilization); and
  surveys, wearables, and genomic variables where appropriate.
- **FR-032**: Every field and mapping exposed by the abstraction MUST be verified against the
  source dataset before being treated as final; unverified items MUST be marked
  `UNVERIFIED / REQUIRES REVIEW` (FR-071).
- **FR-033**: The abstraction MUST support derived historical features where longitudinal data
  allows: latest, previous, change from previous, percent change, rolling mean, minimum, maximum,
  standard deviation, slope, measurement count, time since last measurement, encounter counts,
  medication history, and condition history — all respecting the index-time cutoff and lookback
  window.
- **FR-034**: The abstraction MUST represent missing data explicitly and MUST account for
  differing feature availability, cohort availability, and longitudinal coverage across
  participants.

#### Specialty datasets and modalities

- **FR-035**: Each specialty dataset MUST be accessed through its own adapter; generic components
  MUST NOT depend on any specific dataset.
- **FR-036**: The framework MUST support these modalities where an approved kit requires them:
  ECG/physiological signals (multi-lead waveforms, signal preprocessing, classification); 2D imaging
  (classification, preprocessing, image-level metadata); 3D imaging (volumetric input,
  segmentation, detection, lesion/nodule characterization); wearable time series (temporal
  measurements, engineered summaries, optional temporal models); genomics (manageable derived
  features, genomic + clinical prediction, dimensionality handling).
- **FR-037**: Adding a dataset, modality, or baseline-template family MUST NOT require redesigning
  generic components (splitting, training workflow, evaluation, calibration, explainability,
  configuration validation, model serialization, prediction interface).

#### Common student workflow

- **FR-040**: Every kit MUST present the same conceptual workflow: (1) clinical problem,
  (2) dataset/cohort, (3) exploratory analysis, (4) preprocessing, (5) baseline model,
  (6) student-developed model, (7) hyperparameter tuning, (8) evaluation, (9) calibration where
  applicable, (10) explainability, (11) final model selection, (12) model completion through the
  standardized prediction interface (FR-095).
- **FR-041**: Kit documentation MUST follow one common structure across all kits and modalities.

#### Baseline models

- **FR-045**: Every kit MUST include a baseline that is understandable, reproducible, and
  appropriate to the task, whose purposes are to prove the pipeline works, establish minimum
  performance, demonstrate the full workflow, and leave meaningful room for improvement.
- **FR-046**: Baselines MUST come from a small, shared set of template families, including as
  needed: binary tabular classification, multiclass tabular classification, longitudinal
  fixed-horizon classification, survival analysis, physiological signal classification,
  wearable/temporal classification, genomic + clinical classification, 2D image classification, 3D
  image classification, image segmentation, and object/nodule detection.

#### ML validity

- **FR-050**: Patient-level splitting — records from one patient MUST NOT appear in more than one
  of train, validation, and test.
- **FR-051**: Temporal integrity — no information occurring after the index time MAY be used as an
  input feature.
- **FR-052**: Target leakage — variables that directly reveal the outcome MUST be identified in the
  kit definition and excluded unless an explicit justification is recorded.
- **FR-053**: Label leakage — outcome construction MUST remain separate from predictor
  construction; data used to define the label MUST NOT become predictor input.
- **FR-054**: Preprocessing isolation — imputation, scaling, encoding, feature selection,
  resampling, and similar steps MUST be learned from training data only.
- **FR-055**: Reproducibility — dataset versions, definition versions, configuration versions,
  random processes, and model settings MUST be recorded so that a baseline run can be repeated
  with the same results on the same data.
- **FR-056**: Calibration — models producing probabilities intended as risk/likelihood MUST have
  calibration evaluated when the kit declares it appropriate.
- **FR-057**: Class imbalance — each kit MUST declare imbalance-appropriate metrics; AUROC alone
  MUST NOT be treated as sufficient when prevalence is low or other metrics are clinically important.
- **FR-058**: Versioned definitions — cohort, phenotype, outcome, and concept-set definitions MUST
  be explicit, versioned, and traceable from every model output.
- **FR-059**: Missingness — missing values MUST be handled by a declared strategy and MUST NOT be
  assumed to represent normal findings.
- **FR-060**: Timeline integrity — longitudinal inputs, index times, lookback windows, and outcomes
  MUST preserve chronological correctness.
- **FR-061**: The framework MUST include automated checks for: patient split integrity, temporal
  cutoff enforcement, target leakage, label leakage, feature mapping, missing-value behavior,
  preprocessing fit isolation, definition validation, output contract validation, model
  save/restore round-trip, and reproducibility.
- **FR-062**: Every kit MUST include kit-specific checks for cohort construction, target
  construction, required features, excluded features, and horizon behavior where applicable.
- **FR-063**: Validity checks MUST use synthetic golden-patient fixtures with known timelines and
  expected derived values (e.g., the creatinine example in User Story 4).

#### Clinical validity

- **FR-070**: The framework MUST NOT contain invented All of Us fields, OMOP mappings, diagnostic
  concept sets, lab mappings, clinical thresholds, disease definitions, outcome definitions, or
  prediction horizons.
- **FR-071**: Any clinical or dataset decision without an authoritative source MUST be marked
  `UNVERIFIED / REQUIRES REVIEW`, in both the kit definition and the kit's documentation; no value
  or mapping MAY be silently invented.
- **FR-072**: Each approved kit MUST cite the source(s) supporting its clinical and dataset
  definitions per the source hierarchy in FR-150.

#### Documentation-first construction and provenance

Applies to all kits — All of Us and specialty (PTB-XL, ISIC, TCIA/LIDC-IDRI, MedMNIST, and later
datasets).

- **FR-150**: Where authoritative documentation exists, kit construction MUST follow it as closely as
  practical, prioritizing sources in this order: (1) official dataset documentation; (2) official
  data dictionaries/codebooks; (3) official OMOP/vocabulary documentation; (4) official clinical
  guidelines or professional-society guidance; (5) validated peer-reviewed phenotype definitions or
  methodological literature; (6) other peer-reviewed research when the above lack detail.
  Undocumented assumptions MUST NOT be substituted for available official guidance.
- **FR-151**: Every important kit-design decision MUST be traceable to its source, including where
  applicable: cohort definition, target/label definition, index date, prediction horizon,
  inclusion and exclusion criteria, OMOP concept mappings, laboratory mappings, units, value
  ranges, clinical thresholds, repeated-measurement requirements, medication definitions,
  diagnosis concept sets, control definitions, preprocessing requirements, dataset-recommended
  train/test splits, patient-grouping requirements, image/signal preprocessing, label provenance,
  missing-value interpretation, and known dataset limitations.
- **FR-152**: Each important definition or mapping MUST carry a provenance record with, where
  practical: source title, source organization, source URL or identifier, source version/date when
  relevant, definition version used by the kit, a short explanation of how the source was applied,
  and verification status. Provenance MUST appear alongside the definition it supports.
- **FR-153**: For All of Us/OMOP kits, each standardized framework feature MUST be traceable through
  feature → OMOP concept or concept set → source table/domain → source documentation, including
  accepted and normalized units (e.g., which measurement concepts represent `creatinine`, which
  units are accepted or converted, and which documentation or validated concept set supports it).
- **FR-154**: Kit construction MUST follow a documented sequence where practical: official
  documentation → clinical/dataset definition → versioned concept sets or mappings → cohort and
  target rules → feature definitions → kit definition (configuration) → notebook/baseline model. The
  kit definition and documentation MUST reflect these decisions directly.
- **FR-155**: Clinical and dataset definitions MUST be visible and inspectable rather than embedded
  in model or notebook code: concept sets versioned and documented; inclusion/exclusion rules
  declarative where practical; target definitions documented separately from model code; notebook
  Markdown explaining how the provided data was constructed.
- **FR-156**: Each kit MUST include construction documentation, following the common structure in
  FR-041, from which a reviewer can answer without reading code: the clinical question; the
  official documentation used; how the cohort, positive labels, and controls were created; the
  index/as-of time; included and deliberately excluded features; how raw fields map to framework
  features; which decisions come directly from documentation versus project-specific
  methodological choices; and which items remain unverified.
- **FR-157**: Any intentional deviation from official documentation or a published definition MUST
  be recorded with the deviation, why it was necessary, and its expected impact; a modified
  definition MUST NOT be presented as the original.
- **FR-158**: A kit MUST NOT be approved while any required clinical or dataset definition is
  `UNVERIFIED / REQUIRES REVIEW`.

#### Candidate and kit approval

- **FR-080**: The framework MUST maintain a kit catalog recording each candidate's status:
  candidate, approved, revised, merged, postponed, replaced, or rejected, with a recorded rationale.
- **FR-081**: Before approval, every core candidate MUST be evaluated for: sample size, positive
  case count, adequate negative/control cases, availability of required features, definability of
  the target, label quality, patient-level structure, longitudinal structure where required,
  manageable class balance, clinical meaningfulness, and non-duplication of another kit (or a
  documented educational reason).
- **FR-082**: Before approval, every specialty kit MUST additionally be evaluated for: dataset
  structure, number of patients, repeated-patient structure, number of samples, label provenance,
  clinical meaning of labels, whether labels represent current state or future outcome,
  train/test leakage risk, feasibility of patient-level splitting, appropriate baseline,
  licensing/access requirements, and educational distinctness from existing kits.
- **FR-083**: Multiple labels in one dataset MUST NOT by themselves justify multiple kits; each kit
  from the same dataset MUST differ in clinical question, target, modeling problem, and educational
  objective.
- **FR-084**: The initial core candidate pool MUST be the 25 candidates listed under "Core All of
  Us Candidate Pool"; the final core catalog targets approximately 20 approved kits, and the
  framework MUST NOT require exactly 20.
- **FR-085**: Each specialty dataset MAY contribute approximately 1–3 kits; this is a guideline,
  not a quota, and there is no fixed total specialty kit count.

#### Standardized prediction contract

- **FR-090**: Every completed model MUST expose a common prediction contract regardless of internal
  implementation, supporting where applicable: model identity, model version, kit identity, dataset
  identity and version, target/clinical condition, prediction type, probability or score, optional
  classification, as-of/index time, optional future horizon, optional per-class probabilities for
  multiclass tasks, relevant input metadata, optional top-feature/explainability information, and
  model metadata (including definition versions per FR-058).
- **FR-091**: The contract MUST be versioned, and outputs MUST declare which contract version they
  conform to.
- **FR-092**: A consumer MUST be able to use outputs from any kit without knowledge of how the model
  was trained.
- **FR-093**: Prediction outputs failing contract validation MUST be rejected with a message
  identifying the unmet requirement.
- **FR-094**: Minimum common envelope for Milestones 1–4 (semantic; concrete schema chosen at
  planning). **Mandatory**: contract version; kit ID; model ID; model version; target/condition;
  prediction type (`current_state` | `future_risk`); as-of/index time; dataset ID; dataset version;
  clinical-definition (phenotype/cohort/target) version; data-environment provenance (e.g.,
  synthetic, public, All of Us Workbench). **Conditional**: probability (required for
  probabilistic binary outputs, null otherwise) with **probability_basis** (required alongside a
  probability; for M1–4 the only value is `development_sample`, meaning the probability reflects
  the kit's sampled model-development prevalence and must not be presented as a population
  disease probability without an appropriate, documented calibration method); score (required for non-probabilistic outputs);
  class label (optional); per-class probabilities (required for multiclass); horizon (required iff
  `future_risk`, MUST be null for `current_state`); calibration status (required when the kit
  declares calibration expectations). **Optional**: input/feature metadata; explainability/top
  features; additional model metadata. The envelope MUST carry an extensible, typed payload slot
  for later specialty outputs (segmentation, detection, survival curves), which are not defined here.

#### Model completion, serialization, and data-environment boundaries

Terminology (canonical; "export" alone MUST NOT be used to imply a trained model can leave its
source environment):

- **Model serialization** — saving/restoring a trained model; permitted to leave its environment
  only when the source dataset's terms allow it.
- **Model completion (submission)** — finishing a model and its evaluation inside the permitted
  environment; for All of Us, the trained model stays in the Researcher Workbench.
- **Portable project definition** — notebooks, kit definition, phenotype definition, feature
  schema, evaluation logic, and model metadata, containing no restricted participant data and no
  prohibited trained artifact.
- **Prediction interface** — the standardized contract (FR-090–FR-094) through which any model's
  outputs are consumed.
- **Demo model** — an artifact trained only on synthetic or otherwise permitted data, used outside
  restricted environments.

- **FR-095**: The framework MUST separate three deliverables: (A) the **research model**, trained,
  evaluated, and kept inside the environment its dataset requires (for All of Us, the Researcher
  Workbench); (B) the **portable project definition**; and (C) **demo models** for external
  dashboards/demos that demonstrate the same prediction contract. This separation is the initial
  architecture.
- **FR-096**: The framework MUST NOT assume a model trained on All of Us participant-level data can
  be downloaded, exported, or moved to an external dashboard, Google Colab, or any other
  environment outside the Researcher Workbench.
- **FR-097**: External dashboards and demos MUST use only demo models and synthetic or otherwise
  permitted data.
- **FR-098**: Synthetic/mock data used outside the Workbench MUST be generated independently of All
  of Us participant data; synthetic data derived from participant data is itself prohibited from
  leaving the Workbench (Data User Code of Conduct).
- **FR-099**: The expected deliverable of an All of Us student project is the research model
  completed and evaluated inside the Workbench, plus its portable project definition; no trained
  All of Us artifact is part of the external deliverable. Whether any Workbench capability exists
  to host, deploy, or serve models MUST be verified with All of Us before being relied on.

#### Dashboard integration (future consumer)

- **FR-100**: The framework MUST support a future research/education dashboard that primarily
  presents current patient assessments based on the most recently available data ("current" means
  the most recent data available to the model, not necessarily real-time information).
- **FR-101**: Where kits provide them, the dashboard MAY additionally present future-risk estimates,
  each labeled with its specific outcome and horizon.
- **FR-102**: The dashboard MUST visibly distinguish current state, future outcome, time horizon,
  and clinical target, and MUST NOT imply that unrelated percentages are comparable.

#### Data protection and disclaimer

- **FR-110**: Real All of Us participant-level data or other restricted clinical data MUST NOT be
  stored in the repository, tests, fixtures, documentation examples, or sample datasets; all
  repository-level testing MUST use synthetic or otherwise permitted data.
- **FR-111**: Work on restricted data MUST occur within the environment and access controls
  required by the relevant dataset.
- **FR-112**: All student-facing materials, prediction outputs' metadata, and the dashboard MUST state
  that outputs are experimental educational/research results and not clinically validated risk
  scores, clinical decision support, diagnoses, or treatment recommendations.

#### Delivery phasing

- **FR-120**: Delivery MUST follow the constitution's milestones: M1 repository foundation; M2
  shared clinical/data abstraction; M3 reusable binary tabular baseline template; M4 three
  reference All of Us kits (Type 2 Diabetes, Chronic Kidney Disease, Hypertension).
- **FR-121**: An architecture review MUST follow M4; core expansion toward ~20 kits MUST NOT begin
  until it confirms the reference-kit criteria (shared architecture works, minimal duplication,
  leakage protections work, synthetic checks pass, standardized output works, kit definitions work,
  no major kit-specific hacks).
- **FR-122**: Specialty kit development MUST begin only after the relevant dataset has passed
  specialty evaluation (FR-082).

#### Notebook delivery and execution

- **FR-140**: Student-facing project files MUST primarily be standard Jupyter notebooks (.ipynb).
- **FR-141**: Google Colab MUST be the preferred execution environment wherever the dataset and its
  data-use rules permit; public/specialty-dataset kits MUST be designed to run in Colab where practical.
- **FR-142**: Notebooks MUST avoid Colab-specific APIs where unnecessary, so they remain runnable in
  any standard Jupyter environment.
- **FR-143**: Each All of Us kit MUST use one portable notebook with a configurable data-source
  adapter: a synthetic/public adapter runnable outside the Workbench (including Colab), and an All
  of Us Workbench adapter for real participant-level analysis inside the Workbench. Paired
  per-environment notebooks MUST NOT be used unless a documented exception (Constitution XXIII)
  shows a single notebook is impractical.
- **FR-144**: No participant-level All of Us data MAY be copied into Colab or any environment
  outside the Researcher Workbench.

#### Notebooks vs shared code

- **FR-145**: Notebooks MUST contain explanatory Markdown, clinical background, EDA,
  visualizations, baseline demonstrations, student work areas, model comparisons, and interpretation.
- **FR-146**: Reusable, tested shared modules MUST contain dataset adapters, feature extraction,
  cohort logic, patient splitting, leakage protection, preprocessing utilities, evaluation
  utilities, configuration validation, and standardized prediction interfaces.
- **FR-147**: Major framework logic MUST NOT be duplicated across notebooks; notebooks call the
  shared modules. This hybrid structure is a formal architectural requirement.

#### Reference kit formulation (Milestone 4: T2D, CKD, Hypertension)

- **FR-130**: Each reference kit MUST be a `current_state` phenotype-inference task: given the
  patient's available non-target-defining clinical information, estimate whether the patient
  currently meets the validated disease phenotype. A positive prediction means "the record is
  consistent with meeting the validated phenotype at the index time"; it is not a diagnosis.
- **FR-131**: For cases, the index time MUST be the date the validated phenotype is first
  established. Input features MUST be available at or before the index time, subject to the final
  leakage rules (FR-137).
- **FR-132**: For controls, the index time MUST be an eligible index/visit date; controls MUST have
  adequate prior observation history and positive evidence sufficient to reasonably classify them as
  controls. Absence of a diagnosis code alone MUST NOT be treated as absence of disease.
- **FR-133**: Information directly used to define the phenotype MUST NOT be used as model input.
  The kit definition MUST declare these target-defining exclusions, and the framework MUST enforce
  them (supporting explicit target-feature exclusion is a required capability of the shared
  architecture).
- **FR-134**: Earlier (pre-index) values of target-defining measurements MUST NOT be used as input
  in the Milestone 4 baselines. Using them is deferred to a later, separate longitudinal/future-risk
  formulation.
- **FR-135**: Initial target-defining exclusions, to be finalized from the verified phenotype
  definitions rather than permanently hard-coded:
  - **T2D**: diabetes diagnoses; HbA1c and glucose measurements used to establish the phenotype;
    diabetes medications used as phenotype evidence.
  - **CKD**: CKD diagnoses; creatinine/eGFR values used to establish the phenotype; urine
    albumin/protein measures used to establish the phenotype; other target-defining kidney evidence.
  - **Hypertension**: hypertension diagnoses; blood-pressure measurements used to establish the
    phenotype; antihypertensive medications where part of the phenotype definition.
- **FR-136**: The following MUST be verified against clinical guidelines, validated EHR phenotype
  literature, and All of Us/OMOP documentation before a reference kit is approved, and remain marked
  `UNVERIFIED / REQUIRES REVIEW` until then: exact phenotype rules; whether repeated evidence is required to
  establish the phenotype; minimum control observation history; control-evidence requirements;
  OMOP concept sets for diagnoses, measurements, and medications.
- **FR-137**: The final leakage rules for each reference kit MUST state how same-day (index-date)
  observations are treated, since non-defining measurements taken during the diagnostic workup may
  carry indirect label information.

### Core All of Us Candidate Pool

Candidate pool (not a mandate; each subject to FR-081):

1. Type 2 Diabetes *(reference kit, M4)*
2. Prediabetes
3. Chronic Kidney Disease *(reference kit, M4)*
4. Acute Kidney Injury
5. Hypertension *(reference kit, M4)*
6. Dyslipidemia
7. Metabolic Syndrome
8. Obesity / Cardiometabolic Risk
9. Coronary Artery Disease
10. Heart Failure
11. Atrial Fibrillation
12. Stroke / Cerebrovascular Disease
13. Anemia
14. Anemia Phenotype / Type
15. Liver Dysfunction
16. Thyroid Dysfunction
17. COPD
18. Asthma
19. Sleep Apnea
20. Osteoporosis
21. Depression
22. Hospital Readmission
23. All-Cause Mortality
24. Wearable Cardiometabolic Health
25. Genomic + Clinical Disease Risk

Selection criteria: data availability, sample size, label quality, clinical relevance,
distinctness, student feasibility, leakage risk, baseline usefulness, and compatibility with the
shared All of Us abstraction.

### Specialty Dataset Candidates

| Dataset | Intended modality / purpose |
|---------|-----------------------------|
| PTB-XL | ECG, physiological signal modeling, 1D deep learning, signal classification |
| ISIC Archive | Dermatology, skin-lesion imaging, image classification, computer vision |
| LIDC-IDRI / TCIA | Lung CT, pulmonary nodules, 3D imaging, segmentation, detection, characterization |
| Additional TCIA collections | Cancer imaging, treatment response, phenotype characterization, prognosis where longitudinal labels exist, multimodal imaging |
| MedMNIST | Introductory biomedical imaging, standardized image classification, lower-barrier deep learning |

No specialty kit is approved by this specification; each requires FR-082 evaluation.

### Key Entities

- **Kit**: A complete student project for one clinical question. Has a kit ID, name, dataset
  reference, template family, prediction type(s), cohort, target, features, prohibited features,
  evaluation expectations, documentation, and kit-specific checks. Belongs to exactly one dataset
  and one template family.
- **Kit Definition**: The declarative description of a kit (FR-010); versioned.
- **Kit Catalog Entry / Approval Record**: A candidate's status, evaluation evidence against
  FR-081/FR-082, decision, and rationale.
- **Dataset**: A data source (All of Us, PTB-XL, ISIC, etc.) with version, access/licensing
  constraints, and patient-level structure.
- **Dataset Adapter**: The isolated boundary translating a dataset into the framework's generic
  representation; one per dataset.
- **Patient Timeline**: Chronologically ordered observations (measurements, conditions,
  medications, procedures, encounters, surveys, wearables) for one patient.
- **Cohort Definition**: Versioned inclusion/exclusion rules defining the kit's population.
- **Target / Outcome Definition**: Versioned rule producing the label; for future-risk kits,
  includes outcome window relative to index time.
- **Concept Set / Phenotype Definition**: Versioned, sourced clinical code sets and rules; carries
  verification status.
- **Feature Definition**: A named input with its source, derivation (e.g., latest, slope), lookback
  window, and missingness handling.
- **Index Time / Lookback Window / Prediction Horizon**: Kit-specific temporal anchors governing
  which data may be used and what is predicted.
- **Partition Assignment**: Patient-level mapping to train/validation/test.
- **Baseline Template Family**: Reusable model template shared by structurally similar kits.
- **Research Model**: A trained model with identity, version, and metadata that remains in the
  environment its source dataset requires (FR-095).
- **Portable Project Definition**: The non-restricted, shareable description of a kit project
  (notebooks, kit definition, phenotype definition, feature schema, evaluation logic, model metadata).
- **Demo Model**: A model trained only on synthetic or permitted data, usable outside restricted
  environments.
- **Data Source Adapter Mode**: The selectable data source for a notebook (synthetic/public vs All
  of Us Workbench).
- **Prediction Output**: One output conforming to the versioned prediction contract (FR-090).
- **Golden Patient Fixture**: Synthetic patient with known timeline and expected derived values.
- **Verification Marker**: The `UNVERIFIED / REQUIRES REVIEW` flag on any clinical or dataset
  decision lacking authoritative source support.
- **Provenance Record**: Source title, organization, URL/identifier, version/date, kit definition
  version, application note, and verification status attached to a definition or mapping (FR-152).
- **Deviation Record**: Documented departure from an official or published definition, with
  reason and expected impact (FR-157).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A student new to the underlying data can run a kit's baseline end-to-end and view its
  evaluation within their first working session (≤ 2 hours), without writing data-mapping,
  splitting, or leakage-prevention code.
- **SC-002**: 100% of approved kits provide every item required by FR-001 (and FR-002 for
  longitudinal kits), confirmed by a documentation completeness review.
- **SC-003**: After the first reference kit, each subsequent structurally similar kit is added with
  zero changes to shared generic components; any kit-specific extension is documented.
- **SC-004**: 100% of approved kits pass the shared validity checks (FR-061) and their kit-specific
  checks (FR-062) on synthetic data before release to students.
- **SC-005**: Each deliberately introduced leakage class in the golden-patient suite (post-index
  observation, cross-partition patient, prohibited feature, label-source feature, non-training
  preprocessing fit) is detected 100% of the time.
- **SC-006**: Re-running any baseline with the same dataset version, definitions, and configuration
  reproduces the recorded evaluation metrics exactly (or within a documented tolerance for
  inherently nondeterministic hardware-dependent methods).
- **SC-007**: Zero real participant-level or restricted records are present in the repository at
  any time.
- **SC-008**: One dashboard consumer displays outputs from demo models of at least three kits of
  different template families without any model-specific logic.
- **SC-016**: Every All of Us kit notebook runs end-to-end in synthetic mode in Google Colab without
  Workbench access, and zero trained All of Us research models or participant-derived data appear in
  any external deliverable.
- **SC-009**: 100% of kit catalog entries — including rejected and postponed candidates — have a
  recorded decision and rationale against the approval criteria.
- **SC-010**: The final core catalog contains approximately 20 approved All of Us kits, every one
  of which met all approval criteria; zero kits are approved with a failing criterion to reach the count.
- **SC-011**: Every approved specialty kit has a completed specialty evaluation record (FR-082), and
  every dataset contributing more than one kit documents how each kit is distinct.
- **SC-012**: 100% of required clinical and dataset definitions in approved kits have a complete
  provenance record (FR-152) and zero are `UNVERIFIED / REQUIRES REVIEW`; in unapproved kits, every
  unsourced item carries that marker.
- **SC-017**: For every approved kit, a reviewer can answer all FR-156 questions from the kit's
  documentation alone, and every All of Us feature can be traced to its concept set, source
  domain, and source documentation (FR-153), confirmed by a documentation audit.
- **SC-013**: 100% of kits in the same template family follow the identical notebook section
  structure, verified by an automated structure check.
- **SC-014**: All three reference kits run end-to-end through the same documented workflow and the
  same shared components; a review finds zero copies of dataset-adapter, cohort, splitting,
  leakage-protection, preprocessing, evaluation, or prediction-contract logic inside kit notebooks.
- **SC-015**: Zero student work areas in any kit require the student to implement raw OMOP mapping,
  patient-level splitting, leakage prevention, or prediction-contract integration.

## Assumptions

- Students have introductory programming and ML knowledge appropriate for a semester-long club or
  course project; the framework does not teach programming from scratch.
- Work on real All of Us data occurs inside the All of Us Researcher Workbench (or equivalent
  approved environment) by users who hold the required access tier; the framework does not provide
  or broker data access.
- Specialty datasets are used under their respective licenses and access terms, which are verified
  during specialty evaluation.
- The repository and local/automated testing run exclusively on synthetic or otherwise permitted data.
- One student (or student team) works on one kit at a time; multi-kit coursework is out of scope.
- "Current" in the dashboard means the most recent data available to the model, not real-time
  clinical feeds; live EHR integration is out of scope.
- The dashboard is a future consumer; its detailed design is a later feature built on the
  prediction contract.
- Student deliverables are standard Jupyter notebooks with Google Colab preferred (FR-140–FR-143).
  Programming language, ML libraries, configuration format, serialization format, deployment
  platform, and detailed architecture are decided at planning, not here.
- All of Us data-use constraints are taken from the Data User Code of Conduct, the Egress Alert
  Policy, and the Data and Statistics Dissemination Policy. The specific statement that models
  trained on participant-level data cannot currently be downloaded is recorded from official
  guidance as quoted by the project owner; its source page was not retrievable during
  clarification and MUST be confirmed (Open Item 9).

## Open Items

These are intentionally unresolved and MUST NOT be settled by assumption. Each is resolved through
the approval and verification processes defined above (FR-032, FR-071, FR-081, FR-082) or in later
specifications.

1. **Final core catalog**: Which ~20 of the 25 candidates become approved kits (pending FR-081
   evaluation on actual All of Us data).
2. **Phenotype definitions**: Exact cohort and phenotype definitions for each kit. For the three
   reference kits the formulation is fixed (FR-130–FR-135); the verification items in FR-136 and
   the same-day rule in FR-137 remain open.
3. **All of Us feature/concept availability**: Which FR-031 fields exist, in what form, with what
   coverage, and their verified concept mappings.
4. **Outcome definitions**: Exact outcome definitions for each kit and each future-risk extension.
5. **Prediction horizons**: Horizons for each future-risk kit, justified by clinical question and data.
6. ~~**Reference-kit prediction types**~~ — *Resolved 2026-10-15*: `current_state` only (FR-130).
7. **Specialty dataset viability**: How many (if any) kits each specialty dataset supports, pending
   FR-082 evaluation.
8. **Dataset-access constraints**: Access tiers, licensing, and data-use agreements for each
   specialty dataset; student access tier needed for the All of Us Workbench. (Synthetic stand-ins
   for All of Us are now required — FR-098, FR-143.)
9. **Model export** — *Partially resolved 2026-10-15*: All of Us research models stay in the
   Workbench (FR-095–FR-099). Still open: official confirmation of the model-download restriction
   text; whether models trained only on dissemination-compliant summary data may leave; whether
   any Workbench hosting/serving capability exists; serialization format for permitted datasets.
10. **Dashboard integration details**: Hosting and presentation design (data source is now fixed
    to synthetic/permitted data and demo models — FR-097). *Deferred.*
11. **Prediction contract schema** — *Partially resolved 2026-10-15*: minimum envelope defined
    (FR-094). Concrete field types and serialization are decided at planning.
12. **Deferred (do not affect Milestones 1–4)**: detailed specialty-kit output payloads; final
    survival-output design; detailed wearable architecture; detailed genomic architecture;
    specialty dataset adapter details; final dashboard UI; phenotype definitions for kits beyond
    the three reference kits.
