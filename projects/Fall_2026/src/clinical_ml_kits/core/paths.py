"""Locate the framework's definition tree (repository checkout or bundled wheel data)."""

from __future__ import annotations

import os
from pathlib import Path

_PKG = Path(__file__).resolve().parents[1]


def project_root() -> Path:
    """Root holding ``kits/``, ``definitions/``, and ``synthetic/``.

    Order: ``CKIT_HOME`` env var; the repository checkout (``src`` layout); the data bundled in
    the installed wheel.
    """
    env = os.environ.get("CKIT_HOME")
    if env:
        return Path(env).resolve()
    checkout = _PKG.parents[1]
    if (checkout / "definitions").is_dir() and (checkout / "kits").is_dir():
        return checkout
    return _PKG / "_bundled"
