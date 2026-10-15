"""Strict ``string.Template`` rendering with indentation-preserving multiline values (ADR-001)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from string import Template

_PATTERN: re.Pattern[str] = Template.pattern


def render(template: str, values: Mapping[str, str]) -> str:
    """Substitute ``$name``/``${name}``; ``$$`` → ``$``. Missing names raise ``KeyError``.

    When a placeholder is preceded on its line only by whitespace, continuation lines of a
    multiline value are indented to the placeholder's column.
    """
    out: list[str] = []
    pos = 0
    for m in _PATTERN.finditer(template):
        out.append(template[pos : m.start()])
        pos = m.end()
        if m.group("escaped") is not None:
            out.append("$")
            continue
        name = m.group("named") or m.group("braced")
        if name is None:
            line = template.count("\n", 0, m.start()) + 1
            raise ValueError(f"invalid placeholder at line {line}: {m.group(0)!r}")
        value = str(values[name])
        line_start = template.rfind("\n", 0, m.start()) + 1
        prefix = template[line_start : m.start()]
        if "\n" in value and prefix.strip() == "":
            value = value.replace("\n", "\n" + prefix)
        out.append(value)
    out.append(template[pos:])
    return "".join(out)


def pyrepr(value: object) -> str:
    """A Python literal that reads naturally in a notebook (double-quoted strings)."""
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(value, (list, tuple)):
        inner = ", ".join(pyrepr(v) for v in value)
        return (
            f"[{inner}]"
            if isinstance(value, list)
            else f"({inner}{',' if len(value) == 1 else ''})"
        )
    if isinstance(value, dict):
        return "{" + ", ".join(f"{pyrepr(k)}: {pyrepr(v)}" for k, v in value.items()) + "}"
    return repr(value)
