"""T045: notebook builder (sections, roles, determinism, nbformat validity)."""

from __future__ import annotations

import ast
from pathlib import Path

import nbformat

from clinical_ml_kits.notebooks.builder import (
    ROLES,
    SECTIONS,
    build_notebook,
    build_setup_check,
    notebook_text,
)

STUB = Path(__file__).resolve().parents[2] / "fixtures" / "notebooks" / "stub_skeleton"
VALUES = {
    "kit_id": '"stub_kit"',
    "question": "Is this a stub?",
    "number": "16",
    "title": "Stub kit",
}


def _nb() -> nbformat.NotebookNode:
    return build_notebook(STUB, VALUES, kit_id="stub_kit", title="Stub kit")


def test_valid_nbformat_v4() -> None:
    nb = _nb()
    assert nb.nbformat == 4
    nbformat.validate(nb)


def test_thirteen_sections_in_order() -> None:
    assert len(SECTIONS) == 13
    nb = _nb()
    headings = [
        c.source.splitlines()[0]
        for c in nb.cells
        if c.cell_type == "markdown" and c.source.startswith("## ")
    ]
    assert headings == [f"## {n}. {t}" for n, t in SECTIONS]


def test_every_cell_tagged() -> None:
    for c in _nb().cells:
        assert c.metadata["ckit_role"] in ROLES


def test_code_cells_have_banner_and_parse() -> None:
    for c in _nb().cells:
        if c.cell_type == "code":
            assert c.source.startswith("# ")
            ast.parse(c.source)


def test_byte_identical_builds() -> None:
    assert notebook_text(_nb()) == notebook_text(_nb())


def test_setup_check_notebook() -> None:
    nb = build_setup_check()
    nbformat.validate(nb)
    src = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
    assert "sys.version_info" in src and "sklearn" in src and "environment" in src.lower()
    for c in nb.cells:
        assert c.metadata["ckit_role"] in ROLES
        if c.cell_type == "code":
            ast.parse(c.source)
