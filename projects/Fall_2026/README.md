# Clinical ML Kit Framework (`clinical_ml_kits`)

Leakage-safe, reusable machine-learning project kits for clinical ML education, built primarily on
the NIH All of Us Research Program (OMOP CDM) with an independent synthetic stand-in for use
outside the All of Us Researcher Workbench.

> **Educational/research use only.** Nothing in this repository is a clinically validated risk
> score, diagnosis, or treatment recommendation. Synthetic data here is artificial and not
> clinically realistic.

- Governing documents: `.specify/memory/constitution.md`, `specs/001-clinical-ml-kit-framework/`.
- Install and tooling: [`docs/dependencies.md`](docs/dependencies.md).
- Conventions: [`docs/conventions.md`](docs/conventions.md).
- Verification status of external facts: [`docs/verification/README.md`](docs/verification/README.md).

## All of Us data boundary

All of Us participant-level data is only ever processed **inside the All of Us Researcher
Workbench**. The All of Us adapter refuses to initialize anywhere else; synthetic mode never
contacts All of Us. No participant-level data, derived rows, group keys, or trained All of Us
models may enter this repository.
