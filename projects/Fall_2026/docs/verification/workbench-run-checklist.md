# Workbench verification run checklist (quickstart § 4) — manual, inside the Researcher Workbench only

Run once per reference kit **after** `ckit validate kits/all_of_us/<kit> --level workbench` passes
(no provisional values), V-03 is verified, and the All of Us adapter queries exist (T126–T127,
blocked on V-10/V-11). Never copy participant-level data out of the Workbench. Record only
V-03-permitted aggregates in `kits/all_of_us/<kit>/evidence/fr081.yaml`.

Kit: ________  CDR version: ________  Date: ________  Operator: ________

| # | Step | Expected result | Pass/Fail | Notes |
|---|---|---|---|---|
| 1 | `ckit validate kits/all_of_us/<kit> --level workbench` (in a checkout) | exit 0 | ☐ PASS ☐ FAIL | |
| 2 | Workbench 2.0 JupyterLab: install the pinned tag with the `[aou]` extra | install succeeds; `python -c "import clinical_ml_kits"` | ☐ PASS ☐ FAIL | |
| 3 | Run `kits/00_setup_check.ipynb` | "All of Us Workbench environment: True (verified markers)" | ☐ PASS ☐ FAIL | |
| 4 | Outside the Workbench (local/Colab): `load_kit(<kit>, data_source="all_of_us")` | `EnvironmentNotPermitted` before any data access | ☐ PASS ☐ FAIL | |
| 5 | In the Workbench: open `kit.ipynb`, set `DATA_SOURCE = "all_of_us"`, run sections 0–2 | cohort, labels, features, and split built; no file written into the checkout | ☐ PASS ☐ FAIL | |
| 6 | Compute FR-081 evidence **inside** the Workbench: eligible persons, positives, eligible controls, class balance, required-feature availability, per-feature missingness/coverage, longitudinal coverage | values displayed in-session only | ☐ PASS ☐ FAIL | |
| 7 | Unit/range sanity: distribution of each measurement by source unit (aggregates only) | no unexpected units; rejected-unit counts reviewed | ☐ PASS ☐ FAIL | |
| 8 | Run sections 3–12 | baseline, tuning, calibration, explainability, single final evaluation complete | ☐ PASS ☐ FAIL | |
| 9 | `kit.save_model(model, <workspace path>, portable=True)` | refused with `PolicyViolation` | ☐ PASS ☐ FAIL | |
| 10 | `kit.save_model(model, <path inside git checkout>)` | refused with `PolicyViolation` | ☐ PASS ☐ FAIL | |
| 11 | `record = kit.complete(model)`; `record.export(policy, definitions)` | counts 1–20 and derivable values shown as `<=20`; written to the workspace only | ☐ PASS ☐ FAIL | |
| 12 | Copy only V-03-permitted aggregates into `evidence/fr081.yaml` (schema: `core/evidence.py::FR081Evidence`) and notes into `verification.yaml`; regenerate `verification_log.md` with `ckit docs` | `FR081Evidence` validates; `ckit docs --check` passes | ☐ PASS ☐ FAIL | |

`fr081.yaml` fields (data-model § 4 FR081Evidence): `kit_id`, `cdr_version`, `run_date`,
`checklist_reference`, `eligible_persons`, `positives`, `eligible_controls`, `class_balance`,
`required_feature_availability` (per feature: `coverage`, `missingness`), `longitudinal_coverage`,
`dissemination_rule` (`aou_dissemination_policy`), `notes`. Suppressed values are written as `"<=20"`.
