"""Seed plumbing: one kit seed drives NumPy and scikit-learn randomness."""

from __future__ import annotations

import numpy as np


def numpy_rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def sklearn_random_state(seed: int) -> int:
    """scikit-learn ``random_state`` derived from the kit seed (kept in 32-bit range)."""
    return int(seed) % (2**32 - 1)


def derive_seed(seed: int, purpose: str) -> int:
    """A stable sub-seed for an independent purpose (e.g., control sampling)."""
    import hashlib

    digest = hashlib.sha256(f"{seed}:{purpose}".encode()).hexdigest()
    return int(digest[:8], 16)
