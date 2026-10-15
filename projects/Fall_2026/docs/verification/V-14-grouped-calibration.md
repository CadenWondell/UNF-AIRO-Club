# V-14 — Does `CalibratedClassifierCV` pass `groups` to a grouped splitter?

| Field | Value |
|---|---|
| Status | **VERIFIED (empirical)** for scikit-learn 1.3.2, 1.6.1 (Colab, V-13), 1.9.1 (maintainer lock). Workbench version unknown (V-12). |
| Checked on | 2026-10-15 |
| Checked by | Claude Code (empirical probe; script below) |
| Structured record | `definitions/sources/v14_grouped_calibration.yaml` |

## Method

`docs/verification/scripts/v14_probe.py` fits `CalibratedClassifierCV(LogisticRegression(),
cv=SpyGroupKFold(5), method="sigmoid").fit(X, y, groups=groups)` with a `GroupKFold` subclass that
records whether `split()` received `groups`, with metadata routing disabled (default) and enabled
(`sklearn.set_config(enable_metadata_routing=True)`). Run under Python 3.12 with each version via
`uv run --no-project --with scikit-learn==<v>`.

## Observed output

```
sklearn 1.6.1   routing=False: ValueError: The 'groups' parameter should not be None.
                routing=True:  fit OK; splitter received groups: [True]
sklearn 1.9.1   routing=False: ValueError: The 'groups' parameter should not be None.
                routing=True:  fit OK; splitter received groups: [True]
sklearn 1.3.2   routing=False: ValueError: The 'groups' parameter should not be None.
                routing=True:  fit OK; splitter received groups: [True]
```

## Findings

- With default settings, `groups` is **not** routed to the splitter; the call fails loudly (it does
  not silently fall back to ungrouped folds in these versions).
- With the global metadata-routing flag enabled, `groups` reaches the splitter.
- Safe native use therefore depends on a global, version-specific configuration, and the Workbench
  scikit-learn version is unverified.

## Decision (selected pattern)

Use the framework helper **`kit.calibrate_grouped(model, method)`** (`grouped_oof_sigmoid` /
`grouped_oof_isotonic`, research R-26): out-of-fold predictions from `kit.cv_splitter()` with
`groups=` on the training partition, a sigmoid/isotonic calibrator fitted on them, applied to the
model refitted on all training data. `grouped_native_*` stays disabled: the V-14 record lists no
scikit-learn version as safe, so kits declaring it fail validation with `PendingVerification("V-14")`.
Notebook content rules reject `CalibratedClassifierCV` without `cv=kit.cv_splitter()` and `groups=`.

## Affected sections

R-26, contracts/kit-definition.md (calibration.method), contracts/student-notebook.md § 10; T089, T090, T116.
