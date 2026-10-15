# Implementation handoff (paused 2026-10-15)

## State
- `main` is green: ruff, mypy, 207 tests (Python 3.12 locally; CI 3.10/3.13 green at run 38776411847).
- Completed: T001–T049, T051–T064 (see `docs/reviews/task-evidence.md`, checkboxes in tasks.md).
- T050: `ckit notebooks` implemented; its done-check needs the toy notebook (T119).
- In progress: **T065–T066** on branch `wip/m2-generator`:
  - `tests/unit/adapters/test_generator.py` and `tests/fixtures/synthetic/generator_params/gen_test.yaml` (written, failing as expected),
  - full `adapters/synthetic_clinical/params.py` schema (written).
  - TODO: write `adapters/synthetic_clinical/generator.py` (`generate(params) -> Population(persons, observations[logical_concept, no concept_id], groups, seed)`, `generate_population(path, definitions_dir)`), have the adapter map logical concepts to SYN codes, upgrade `tests/fixtures/synthetic/generator_params/fixture_kit.yaml` to a full params file (the strict schema rejects the header-only stub), write `synthetic/generator_params/default.yaml` + README.

## Design decisions already made (keep)
- Fixture kits (incl. future toy kit) use `--root tests/fixtures` (fixture definitions `fx_*`); project kits use the project root.
- Index times are date precision; `same_day: include` admits the whole index day, `exclude_index_day` compares dates.
- AoU adapter must fail closed: V-10 record lists no markers, so `EnvironmentNotPermitted` everywhere.
- V-03 verified (counts 1–20 restricted, from `definitions/sources/aou_dissemination_policy.yaml`).
- Clinical items are never self-verified: researched values stay provisional/`requires_verification`.
- Always chain gates with `&&` before `git commit`.

## Blockers (manual)
V-01/02/04 support ticket; V-10/V-11/V-12 need Workbench access (blocks T126–T127 and Workbench runs T142/T157/T172).
