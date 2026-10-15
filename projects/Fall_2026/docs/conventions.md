# Conventions

## Notebook cell roles (`metadata.ckit_role`)

| Role | Banner (first line of the cell) | Purpose | Editable |
|---|---|---|---|
| `framework` | `# Framework — do not edit` | Setup, `load_kit`, leakage checks, `final_evaluation`, completion | No (restorable by `ckit notebooks`; hash recorded) |
| `baseline` | `# Baseline — working example` | Visible scikit-learn code that builds, fits, predicts, evaluates the baseline | Read/modify; copy into student cells to keep the comparison point |
| `student` | `# Your work` | Runnable starter code (alternative models, tuning grids) | Yes |
| `markdown` | — | Background, construction narrative, expected outputs, interpretation prompts (generated from KitDocs) | Regenerated |

Other banners:

- Provisional values: **`PROVISIONAL — synthetic-only, not an approved clinical definition`**.
- Synthetic mode: **`SYNTHETIC DATA — artificial, not clinically realistic, not derived from any participant data`**.
- Disclaimer (also the envelope constant): *Educational/research output. Not a clinically validated
  risk score, diagnosis, or treatment recommendation.*

## Notebook sections (Template A, in order)

0 Setup · 1 Clinical problem · 2 Dataset and cohort · 3 Exploratory data analysis · 4 Preprocessing ·
5 Baseline model · 6 Evaluate the baseline · 7 Your model · 8 Hyperparameter tuning ·
9 Model comparison · 10 Calibration · 11 Explainability · 12 Final selection and completion.
(13 sections, numbered 0–12; they cover the 12 FR-040 workflow steps.)

## Documentation conventions

- Every kit has the six KitDocs files (`docs/templates/kit_docs/`): `README.md`,
  `clinical_background.md`, `construction.md`, `features.md`, `limitations.md`, and the generated,
  read-only `verification_log.md` (`ckit docs`).
- Facts are written once: notebook Markdown is pulled from KitDocs; verification status lives only in
  the structured YAML (inline ProvenanceRefs and value states).
- Unverified items are marked **`UNVERIFIED / REQUIRES REVIEW`** in YAML (sentinel `UNVERIFIED`) and
  in docs.
- Never describe a probability as a clinical risk score; never describe synthetic data as realistic.

## Source tiers (FR-150)

| Tier | Source type |
|---|---|
| 1 | Official dataset documentation (e.g., All of Us policies, support hub, data browser) |
| 2 | Official data dictionaries / codebooks |
| 3 | Official OMOP / vocabulary documentation (OHDSI, Athena) |
| 4 | Official clinical guidelines / professional-society guidance (ADA, KDIGO, ACC/AHA) |
| 5 | Validated peer-reviewed phenotype definitions or methodological literature (e.g., PheKB/eMERGE) |
| 6 | Other peer-reviewed research or third-party documentation (requires a note explaining why tiers 1–4 were insufficient; P-9) |

## Value states

`verified` (plain value + verified ProvenanceRef) · `provisional` (`{provisional, note, pending}`;
synthetic-only) · `UNVERIFIED` (sentinel). See `specs/001-clinical-ml-kit-framework/contracts/kit-definition.md`.
