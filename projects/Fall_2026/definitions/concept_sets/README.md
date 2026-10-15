# Concept-set realizations

Kits, phenotypes, and the feature registry reference **logical concepts**
(`definitions/concepts/<logical_id>.yaml`, clinical-meaning provenance). Each data source realizes a
logical concept in its own namespace:

```
definitions/concept_sets/<namespace>/<logical_id>/<semver>.yaml
```

| Namespace | Used by | Members |
|---|---|---|
| `synthetic` | synthetic adapter (Colab, CI) | fictional `SYN-` codes; header `synthetic; not real OMOP concepts` |
| `omop` | All of Us adapter (Workbench only) | OMOP concept IDs, **empty until verified** (P-5); mapping provenance required |

Rules:

- A realization's `domain` equals its logical concept's domain.
- `omop` realizations resolve only with verified mapping provenance; otherwise the adapter raises
  `PendingVerification`. No OMOP concept ID is entered without verification.
- `SYN-` codes are invented for software testing and are never presented as OMOP concepts.
- Clinical-meaning provenance lives on the logical concept; mapping provenance on the realization.
- Units: `accepted_units` (`unit`, `factor_to_canonical`) and `canonical_unit` are listed on the
  realization; clinical units/ranges remain provisional or `UNVERIFIED` pending V-25.

This directory documents representation and versioning only; it defines no clinical concept set.
