"""Generate executable kit notebooks from template-family skeletons (plan § 10, ADR-001).

nbformat is imported lazily: generation needs the ``[dev]`` extra, running notebooks does not.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from clinical_ml_kits.notebooks.render import pyrepr, render

SKELETONS = Path(__file__).resolve().parent / "skeletons"
COMMON = SKELETONS / "_common"

SECTIONS: tuple[tuple[int, str], ...] = (
    (0, "Setup"),
    (1, "Clinical problem"),
    (2, "Dataset and cohort"),
    (3, "Exploratory data analysis"),
    (4, "Preprocessing"),
    (5, "Baseline model"),
    (6, "Evaluate the baseline"),
    (7, "Your model"),
    (8, "Hyperparameter tuning"),
    (9, "Model comparison"),
    (10, "Calibration"),
    (11, "Explainability"),
    (12, "Final selection and completion"),
)
ROLES = ("framework", "baseline", "student", "markdown")
BANNERS = {
    "framework": "# Framework — do not edit",
    "baseline": "# Baseline — working example",
    "student": "# Your work",
}
# Pinned framework release installed by notebooks when the package is not present.
INSTALL_TAG = "v0.1.0"
INSTALL_SPEC = (
    "clinical-ml-kits @ git+https://github.com/CadenWondell/UNF-AIRO-Club.git"
    f"@{INSTALL_TAG}#subdirectory=projects/Fall_2026"
)


def _nbformat() -> Any:
    try:
        import nbformat
    except ImportError as e:  # pragma: no cover - exercised only without the dev extra
        raise RuntimeError("notebook generation needs the [dev] extra (nbformat)") from e
    return nbformat


def _cell(kind: str, role: str, source: str, cell_id: str, section: int | None) -> Any:
    nbf = _nbformat()
    meta: dict[str, Any] = {"ckit_role": role}
    if section is not None:
        meta["ckit_section"] = section
    if kind == "code":
        body = source.rstrip("\n")
        banner = BANNERS[role]
        text = body if body.startswith(banner) else f"{banner}\n{body}"
        c = nbf.v4.new_code_cell(text, metadata=meta)
    else:
        c = nbf.v4.new_markdown_cell(source.rstrip("\n"), metadata=meta)
    c["id"] = cell_id
    return c


def _new_notebook(cells: list[Any], extra_meta: dict[str, Any]) -> Any:
    nbf = _nbformat()
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "ckit": extra_meta,
    }
    nb.nbformat, nb.nbformat_minor = 4, 5
    return nb


def load_skeleton(skeleton_dir: Path) -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load((Path(skeleton_dir) / "skeleton.yaml").read_text())
    for i, c in enumerate(data["cells"]):
        if c["role"] not in ROLES:
            raise ValueError(f"cell {i}: unknown role {c['role']!r}")
        if c["section"] not in {n for n, _ in SECTIONS}:
            raise ValueError(f"cell {i}: unknown section {c['section']!r}")
    return data


def build_notebook(
    skeleton_dir: Path,
    values: dict[str, str],
    *,
    kit_id: str,
    title: str,
    extra_meta: dict[str, Any] | None = None,
) -> Any:
    """Render a skeleton into a notebook: title, 13 section headings, and tagged cells."""
    skel = load_skeleton(skeleton_dir)
    vals = {
        "title": title,
        "kit_id_literal": pyrepr(kit_id),
        "install_spec": pyrepr(INSTALL_SPEC),
        **values,
    }
    vals.setdefault("kit_id", kit_id)
    vals.setdefault("template_family", skel["template_family"])
    vals.setdefault("prediction_type", "current_state")
    vals.setdefault(
        "disclaimer",
        "Educational/research output. Not a clinically validated risk score, diagnosis, or "
        "treatment recommendation.",
    )
    cells = [
        _cell(
            "markdown",
            "markdown",
            render((COMMON / "title.md").read_text(), vals),
            "ckit-title",
            None,
        )
    ]
    by_section: dict[int, list[dict[str, Any]]] = {}
    for c in skel["cells"]:
        by_section.setdefault(int(c["section"]), []).append(c)
    for n, name in SECTIONS:
        intro = render(skel.get("section_intros", {}).get(n, ""), vals).strip()
        heading = f"## {n}. {name}" + (f"\n\n{intro}" if intro else "")
        cells.append(_cell("markdown", "markdown", heading, f"ckit-{n:02d}-000", n))
        for i, c in enumerate(by_section.get(n, []), start=1):
            kind = "markdown" if c["role"] == "markdown" else "code"
            src = render(c["source"], vals)
            cells.append(_cell(kind, c["role"], src, f"ckit-{n:02d}-{i:03d}", n))
    meta = {
        "kit_id": kit_id,
        "template_family": skel["template_family"],
        "generated_by": "ckit notebooks",
        **(extra_meta or {}),
    }
    nb = _new_notebook(cells, meta)
    _nbformat().validate(nb)
    return nb


def build_setup_check() -> Any:
    data = yaml.safe_load((COMMON / "setup_check.yaml").read_text())
    vals = {"install_spec": pyrepr(INSTALL_SPEC)}
    cells = []
    for i, c in enumerate(data["cells"]):
        kind = "markdown" if c["role"] == "markdown" else "code"
        cells.append(_cell(kind, c["role"], render(c["source"], vals), f"ckit-setup-{i:03d}", None))
    nb = _new_notebook(cells, {"notebook": "00_setup_check", "generated_by": "ckit notebooks"})
    _nbformat().validate(nb)
    return nb


def notebook_text(nb: Any) -> str:
    """Deterministic serialization (outputs stripped, stable key order)."""
    nbf = _nbformat()
    for c in nb.cells:
        if c.cell_type == "code":
            c.outputs = []
            c.execution_count = None
    return str(nbf.writes(nb)) + "\n"


def cell_hashes(nb: Any) -> dict[str, str]:
    """SHA-256 of each framework cell's source (recorded in the RunManifest at run time)."""
    return {
        c["id"]: hashlib.sha256(c.source.encode()).hexdigest()
        for c in nb.cells
        if c.metadata.get("ckit_role") == "framework"
    }
