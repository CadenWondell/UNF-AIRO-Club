"""T043: stdlib string.Template rendering rules (ADR-001)."""

from __future__ import annotations

import ast

import pytest

from clinical_ml_kits.notebooks.render import render


def test_dollar_escape_braces_and_quotes_survive() -> None:
    tpl = 'price = "$$5"\nd = {"a": [1, 2]}\ns = f"{x!r}" + \'q\'\n'
    out = render(tpl, {})
    assert out == 'price = "$5"\nd = {"a": [1, 2]}\ns = f"{x!r}" + \'q\'\n'


def test_named_and_braced_placeholders() -> None:
    assert render("a=$x b=${y}z", {"x": "1", "y": "2"}) == "a=1 b=2z"


def test_multiline_value_keeps_indentation() -> None:
    tpl = "def f():\n    $body\n    return 1\n"
    out = render(tpl, {"body": "a = 1\nb = 2"})
    assert out == "def f():\n    a = 1\n    b = 2\n    return 1\n"
    ast.parse(out)


def test_missing_variable_raises() -> None:
    with pytest.raises(KeyError):
        render("x = $missing", {})


def test_invalid_placeholder_raises() -> None:
    with pytest.raises(ValueError):
        render("x = $1abc", {})


def test_deterministic() -> None:
    tpl = "m = LogisticRegression(C=$C, penalty=$penalty)\n"
    vals = {"C": "1.0", "penalty": '"l2"'}
    assert render(tpl, vals) == render(tpl, dict(reversed(list(vals.items()))))
    ast.parse(render(tpl, vals))
