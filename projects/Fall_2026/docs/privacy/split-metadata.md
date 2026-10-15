# Split and grouping metadata: what is persisted, and where

| Item | Content | Synthetic mode | All of Us Workbench |
|---|---|---|---|
| Split assignment | partition per person, recomputed from SHA-256(salt + person_id) on every load | not persisted (recomputed) | not persisted; may be cached only inside the workspace, **never** in the repository |
| SplitManifest | strategy, salt, salt_version, kit_version, fractions, assignment digest, sampled development prevalence, per-partition `n`, `n_pos`, prevalence | may be saved anywhere | stays in the workspace; any copy leaving the Workbench (completion record, FR-081 evidence, repository) passes the V-03 dissemination filter: counts 1–20 and values that reveal them are suppressed |
| Patient groups (`groups`) | SHA-256("group:" + salt + person_id), truncated; pseudonymous and participant-derived | in memory only | in memory only; **never written**, never displayed (masked repr), never a column of `X`, never in envelopes or completion records |
| Person IDs | — | synthetic `SYN-` IDs may appear | never leave the session |

The manifest never contains person IDs or group keys (tested in `tests/leakage/test_split.py`).
The salt is fixed per kit and versioned; changing it to improve outcome balance is prohibited.
Rules of V-03: `docs/verification/V-03-small-counts.md`.
