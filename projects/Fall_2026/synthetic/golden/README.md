# Golden-patient fixtures

Small, hand-authored, **independently synthetic** patient timelines with known expected values.
They serve deterministic unit, edge-case, temporal, and leakage tests only. Kit notebooks never run
on golden fixtures: `data_source="synthetic"` loads a kit's generated population
(`synthetic/generator_params/<kit_id>.yaml`) instead.

## Format (`*.yaml`)

```yaml
provenance: "independently authored synthetic; not derived from any participant data"   # required
fixture: <name>
description: <what the fixture exercises>
persons:        # person_id, birth_date, sex_at_birth, observation_start, observation_end
observations:   # person_id, domain, concept_id (SYN- code), value_num, value_concept, unit_raw,
                # start_time (date or ISO datetime), end_time, time_precision (date|datetime),
                # visit_id, optional fixture-only "label"
index:          # person_id, index_time, index_visit_id (optional)
expected:       # free-form expected values consumed by tests
rules:          # (kit fixtures) which rules the fixture exercises and their value state
```

Rules:

- Every identifier (person, concept, sex code) is a fictional `SYN-` identifier. `SYN-` codes are
  **not** OMOP concepts.
- Values are invented to exercise software behavior; they are not clinically realistic and are not
  derived from All of Us or any participant data.
- Kit-specific fixtures live in `synthetic/golden/<kit>/` and state which rules are verified or
  provisional.
