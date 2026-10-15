"""Notebook content rules (contracts/student-notebook.md § Validation).

Rules:
  NB-01 framework cells construct no estimator and set no hyperparameters
  NB-02 baseline cells construct a standard estimator and call ``.fit(``
  NB-03 no SQL and no BigQuery client in any cell
  NB-04 no raw data-file reads (``pd.read_*``, ``open(``, ``np.load*``)
  NB-05 no split construction (train_test_split, *KFold, *ShuffleSplit, …)
  NB-06 model selection / CV / calibration only with ``cv=kit.cv_splitter()`` and ``groups=``
  NB-07 ``groups`` only ever passed as ``groups=…`` (never displayed or added to ``X``)
  NB-08 no imports from ``clinical_ml_kits.adapters``
  NB-09 no ``TODO``, ``...``, or ``NotImplementedError`` in framework/baseline cells
  NB-10 every cell carries a valid ``ckit_role``
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

ROLES = {"framework", "baseline", "student", "markdown"}
ESTIMATOR = re.compile(
    r"^(LogisticRegression\w*|\w*Classifier|\w*Regressor|SVC|SVR|LinearSVC|NuSVC|\w*NB|"
    r"KNeighbors\w*|LinearDiscriminantAnalysis|QuadraticDiscriminantAnalysis|Perceptron|"
    r"RidgeClassifier\w*|SGD\w*|MLP\w*)$"
)
SPLITTERS = {
    "train_test_split",
    "KFold",
    "StratifiedKFold",
    "GroupKFold",
    "StratifiedGroupKFold",
    "RepeatedKFold",
    "RepeatedStratifiedKFold",
    "ShuffleSplit",
    "StratifiedShuffleSplit",
    "GroupShuffleSplit",
    "LeaveOneOut",
    "LeavePOut",
    "LeaveOneGroupOut",
    "LeavePGroupsOut",
    "PredefinedSplit",
    "TimeSeriesSplit",
}
SEARCHES = {
    "GridSearchCV",
    "RandomizedSearchCV",
    "HalvingGridSearchCV",
    "HalvingRandomSearchCV",
    "CalibratedClassifierCV",
}
CV_FUNCS = {
    "cross_val_score",
    "cross_validate",
    "cross_val_predict",
    "learning_curve",
    "validation_curve",
    "permutation_test_score",
}
READERS = re.compile(
    r"^(read_(csv|parquet|table|excel|feather|json|sql\w*|pickle|hdf|sas|stata|"
    r"spss|orc|fwf)|open|load|loadtxt|genfromtxt|fromfile|load_npz)$"
)
SQL = re.compile(r"\bselect\b[\s\S]+\bfrom\b|\binsert\s+into\b|\bcreate\s+table\b", re.I)


@dataclass(frozen=True)
class Violation:
    rule: str
    cell_id: str
    message: str

    def __str__(self) -> str:
        return f"{self.rule} [{self.cell_id}] {self.message}"


def _name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _is_cv_splitter_call(node: ast.expr | None, cv_names: set[str]) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Name):
        return node.id in cv_names
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "cv_splitter"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "kit"
    )


def _kw(call: ast.Call, name: str) -> ast.expr | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _source(cell: dict[str, Any]) -> str:
    src = cell.get("source", "")
    return "".join(src) if isinstance(src, list) else str(src)


def check_notebook(nb: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    trees: list[tuple[str, str, ast.Module]] = []
    for i, cell in enumerate(nb.get("cells", [])):
        cid = str(cell.get("id", i))
        role = (cell.get("metadata") or {}).get("ckit_role")
        if role not in ROLES:
            out.append(Violation("NB-10", cid, f"missing or invalid ckit_role {role!r}"))
            continue
        if cell.get("cell_type") != "code":
            continue
        src = _source(cell)
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            out.append(Violation("NB-10", cid, f"code cell does not parse: {e}"))
            continue
        trees.append((cid, role, tree))
        if role in ("framework", "baseline"):
            if re.search(r"\bTODO\b", src) or "NotImplementedError" in src:
                out.append(Violation("NB-09", cid, "placeholder token in a protected cell"))
            if any(isinstance(n, ast.Constant) and n.value is Ellipsis for n in ast.walk(tree)):
                out.append(Violation("NB-09", cid, "'...' placeholder in a protected cell"))

    cv_names: set[str] = set()
    for _, _, tree in trees:
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and _is_cv_splitter_call(n.value, set()):
                cv_names |= {t.id for t in n.targets if isinstance(t, ast.Name)}

    search_vars: dict[str, str] = {}  # variable -> cell id of its unsafe-until-fitted search
    fitted_with_groups: set[str] = set()
    baseline_estimator = baseline_fit = False
    for cid, role, tree in trees:
        for n in ast.walk(tree):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
                if any(m.startswith("clinical_ml_kits.adapters") for m in mods):
                    out.append(Violation("NB-08", cid, "imports adapter internals"))
                if any(m.startswith("google.cloud") or "bigquery" in m for m in mods):
                    out.append(Violation("NB-03", cid, "BigQuery/Cloud client import"))
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and SQL.search(n.value):
                out.append(Violation("NB-03", cid, "SQL text in a cell"))
            if not isinstance(n, ast.Call):
                continue
            name = _name(n.func)
            if ESTIMATOR.match(name):
                if role == "framework":
                    out.append(Violation("NB-01", cid, f"framework cell constructs {name}"))
                if role == "baseline":
                    baseline_estimator = True
            if name == "fit" and role == "baseline":
                baseline_fit = True
            if READERS.match(name) and (
                name != "load"
                or _name(getattr(n.func, "value", n)) in ("np", "numpy", "pickle", "joblib", "json")
            ):
                out.append(Violation("NB-04", cid, f"raw data read via {name}()"))
            if name in SPLITTERS:
                out.append(Violation("NB-05", cid, f"split construction {name}()"))
            if name in SEARCHES or name in CV_FUNCS:
                if not _is_cv_splitter_call(_kw(n, "cv"), cv_names):
                    out.append(Violation("NB-06", cid, f"{name} without cv=kit.cv_splitter()"))
                if name in CV_FUNCS and _kw(n, "groups") is None:
                    out.append(Violation("NB-06", cid, f"{name} without groups="))
            if name == "fit" and isinstance(n.func, ast.Attribute):
                target = n.func.value
                has_groups = _kw(n, "groups") is not None
                if isinstance(target, ast.Call) and _name(target.func) in SEARCHES:
                    if not has_groups:
                        out.append(
                            Violation("NB-06", cid, f"{_name(target.func)}.fit without groups=")
                        )
                elif isinstance(target, ast.Name) and has_groups:
                    fitted_with_groups.add(target.id)
        for n in ast.walk(tree):
            if (
                isinstance(n, ast.Assign)
                and isinstance(n.value, ast.Call)
                and _name(n.value.func) in SEARCHES
            ):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        search_vars[t.id] = cid
        out += _groups_usage(cid, tree)
    for var, cid in search_vars.items():
        if var not in fitted_with_groups:
            out.append(Violation("NB-06", cid, f"{var}.fit(...) never passes groups="))
    if any(role == "baseline" for _, role, _ in trees) and not (
        baseline_estimator and baseline_fit
    ):
        out.append(
            Violation(
                "NB-02", "baseline", "baseline cells must construct an estimator and call .fit("
            )
        )
    return out


def _groups_usage(cid: str, tree: ast.Module) -> list[Violation]:
    """``.groups`` may only appear as the value of a ``groups=`` keyword argument."""
    allowed: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            for k in n.keywords:
                if k.arg == "groups":
                    allowed |= {id(x) for x in ast.walk(k.value)}
    return [
        Violation("NB-07", cid, "patient groups used outside a groups= argument")
        for n in ast.walk(tree)
        if isinstance(n, ast.Attribute) and n.attr == "groups" and id(n) not in allowed
    ]
