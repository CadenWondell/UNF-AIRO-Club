"""Opaque patient grouping keys (data-model § 4).

``groups`` = truncated SHA-256("group:" + salt + person_id): identical for every row of a person,
distinct across persons (collisions are checked), deterministic. It is pseudonymous and
participant-derived: never a feature, never displayed, never written in envelopes or records.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import numpy as np

KEY_HEX = 24


if TYPE_CHECKING:
    _ArrayBase = np.ndarray[Any, Any]
else:
    _ArrayBase = np.ndarray


class OpaqueGroups(_ArrayBase):
    """A NumPy array of group keys whose printed form never shows the keys."""

    def __new__(cls, keys: Sequence[str]) -> OpaqueGroups:
        return np.asarray(list(keys), dtype=object).view(cls)

    def __repr__(self) -> str:
        return f"<masked patient groups: n={self.size}, unique={len(set(self.tolist()))}>"

    __str__ = __repr__

    def _repr_html_(self) -> str:
        return repr(self).replace("<", "&lt;").replace(">", "&gt;")

    def __array_wrap__(self, obj: Any, context: Any = None, return_scalar: bool = False) -> Any:
        return obj


def group_keys(person_ids: Sequence[str], salt: str) -> OpaqueGroups:
    ids = [str(p) for p in person_ids]
    cache: dict[str, str] = {}
    for p in dict.fromkeys(ids):
        cache[p] = hashlib.sha256(f"group:{salt}{p}".encode()).hexdigest()[:KEY_HEX]
    if len(set(cache.values())) != len(cache):
        raise ValueError("patient group key collision; increase KEY_HEX")
    return OpaqueGroups([cache[p] for p in ids])
