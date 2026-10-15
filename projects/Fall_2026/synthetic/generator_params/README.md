# Synthetic population parameters

One params file per kit (`<kit_id>.yaml`) drives the seeded generator
(`clinical_ml_kits.adapters.synthetic_clinical.generator`) that produces the population used for
**end-to-end model and notebook execution** in synthetic mode (`data_source="synthetic"`).
Golden fixtures (`synthetic/golden/`) are separate: they serve deterministic unit and edge-case
tests and are never used by kit notebooks.

Every params file:

- starts with the header `artificial: true`, `clinically_realistic: false`,
  `derived_from_participant_data: false`, and the purpose statement
  "framework testing and student workflow only; not a prevalence or effect-size simulation"
  (validated; files without it are rejected);
- is invented for software testing: it is never fitted to, sampled from, or tuned against All of Us
  or any participant data, and makes no attempt to reproduce participant distributions;
- lists every deliberately planted case/control difference under `planted_relationships`
  (validated);
- uses logical concept ids; the synthetic adapter maps them to fictional `SYN-` codes, which are not
  OMOP concepts.

Main sections: `seed`, `n_persons`, `calendar`, `person`, `case_fraction` (the generator's recipe
group, not a label: labels come from the kit's phenotype rules), `anchor`, `visit_density`,
`measurements` (per-visit values and missingness), `conditions`, `events` (`case_recipe`,
`control_recipe`, `background`, `exclusions`, `workup_at_onset`), `planted_relationships`.
