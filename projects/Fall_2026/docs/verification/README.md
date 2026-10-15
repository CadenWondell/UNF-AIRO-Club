# Verification index

Status of every external-fact verification item (plan.md § 21). A task blocked on an item must not
encode an assumption in its place. Classification: **A** implementation blocker · **B** approval /
Workbench blocker only · **C** deferred / documentation only.

| ID | Topic | Status | Class | Record | Manual action |
|---|---|---|---|---|---|
| V-01 | Model export from the Workbench | UNCONFIRMED | C | [V-01](V-01-model-export.md) | All of Us support ticket |
| V-02 | Models trained on summary data | UNCONFIRMED | C | [V-02](V-02-summary-models.md) | Same ticket |
| V-03 | Small-count dissemination rule | VERIFIED (tier 1 policy text) | — | [V-03](V-03-small-counts.md) | Maintainer confirmation recommended |
| V-04 | Workbench model hosting/serving | UNCONFIRMED | C | [V-04](V-04-workbench-hosting.md) | Same ticket |
| V-10 | Workbench data-access pattern, CDR naming | UNRESOLVED | A for AoU adapter SQL (T126–T127); B for Workbench runs | [V-10](V-10-workbench-access.md) | Inspect a Workbench 2.0 JupyterLab kernel |
| V-11 | Populated OMOP tables/fields | UNRESOLVED | A for AoU adapter SQL; B for Workbench runs | [V-11](V-11-omop-coverage.md) | CDR v8 data dictionary (registered users) |
| V-12 | Workbench runtime versions | UNRESOLVED | B (CI uses floor 3.10 instead) | [V-12](V-12-workbench-runtime.md) | `python -V`, `pip list` in the Workbench |
| V-13 | Colab runtime versions | VERIFIED | — | [V-13](V-13-colab-runtime.md) | — |

Reconciliation (T015, 2026-10-15): research.md R-01, R-15, R-17 and plan.md § 21 were updated with
these results. No result contradicts the approved architecture: V-01/V-02/V-04 confirm the
no-export design assumption is still required; V-03 provides the dissemination parameters the
architecture left open; V-10 changes how the Workbench is detected, which the design already
delegated to V-10 (the guard fails closed until verified); V-13 moves the Colab Python to 3.13,
which `requires-python >= 3.10` already admits.
