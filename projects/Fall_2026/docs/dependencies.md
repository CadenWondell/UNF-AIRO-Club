# Dependencies and installation

## Extras

| Extra | Contents | Who needs it |
|---|---|---|
| (runtime) | numpy, pandas, scikit-learn, pydantic v2, PyYAML, matplotlib (joblib via scikit-learn) | Everyone, including students |
| `[dev]` | pytest, nbmake, nbformat, nbclient, ipykernel, nbstripout, ruff, mypy, types-PyYAML, pre-commit | Maintainers and CI only |
| `[aou]` | **Empty, pending V-10** (the documented Workbench 2.0 client library has not been verified) | All of Us Workbench users, once V-10 is resolved |

## Maintainer install

```bash
cd projects/Fall_2026
uv sync --all-extras                 # locked dev environment from uv.lock
uv run pytest                        # tests
uv run ckit validate --all           # kit definitions + provenance
uv run ckit notebooks --check        # notebook drift
uv run ckit docs --check             # generated verification logs are current
```

## Student / Colab install (synthetic mode)

The first notebook cell installs a pinned tag of the framework:

```python
%pip install "clinical-ml-kits @ git+https://github.com/CadenWondell/UNF-AIRO-Club.git@<tag>#subdirectory=projects/Fall_2026"
```

Kit definitions, logical concepts, and synthetic generator settings are bundled into the wheel, so
`load_kit(...)` works after a plain `pip install`.

## Version-pin strategy

Runtime dependencies use compatible ranges (`>=x.y,<next-major`) so `%pip install` coexists with the
libraries preinstalled in Colab (V-13: Python 3.13, scikit-learn 1.6.1, pandas 2.2.3, numpy 2.1.3)
and the Workbench (V-12, unverified). `uv.lock` pins the exact maintainer environment; it is not used
by students.

## Rules

- Maintainer tooling is never required at student runtime. `import clinical_ml_kits` and running a
  student notebook need only the runtime dependencies.
- Notebook and documentation generation (`ckit notebooks`, `ckit docs`) need the `[dev]` extra:
  nbformat is imported lazily inside the notebook builder only.
- PyTorch is not a dependency in Milestones 1–4.

## scikit-learn upper bound

`scikit-learn>=1.3,<1.10`. Kit notebooks render `LogisticRegression(..., penalty="l2", ...)`
literally from `kit.yaml` (contracts/student-notebook.md). scikit-learn 1.8 deprecated `penalty`
(FutureWarning) and 1.10 removes it, while Colab ships 1.6.1 (V-13), which does not accept the
replacement `l1_ratio`-only form for plain L2. Before raising the cap, migrate the baseline
parameter allow-list and the rendered call together (ADR + contract update).
