# Implementation status (2026-10-15)

Milestones 1–4 are implemented; the post-M4 review outcome is **CONDITIONAL PASS**
(`docs/reviews/post-m4-review.md`). Do not start Milestone 5 until remediation R1 (push the `v0.1.0`
tag and run each kit notebook in Google Colab) and R2 (maintainer sign-off) are closed.

- Task status: 178/183 complete; T126–T127 blocked (V-10/V-11); T142/T157/T172 deferred (Workbench runs need verified definitions and the All of Us query layer). Evidence: `docs/reviews/task-evidence.md`.
- Verification status: `docs/verification/README.md`.
- All three reference kits are `requires_verification` with provisional, labeled values.

Working conventions kept: fixture kits use `--root tests/fixtures`; index times are date precision;
the All of Us adapter fails closed until V-10 lists verified Workbench markers; clinical items are
never self-verified; validation gates are chained so a failure stops the commit.
