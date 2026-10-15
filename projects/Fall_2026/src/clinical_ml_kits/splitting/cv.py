"""Patient-grouped cross-validation splitter for tuning within the training partition."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold


class PatientGroupedKFold(StratifiedGroupKFold):  # type: ignore[misc]
    """``StratifiedGroupKFold`` that refuses to split without patient groups."""

    def split(self, X: Any, y: Any = None, groups: Any = None) -> Iterator[Any]:
        if groups is None:
            raise ValueError(
                "patient groups are required: pass groups=data.train.groups so no patient "
                "appears on both sides of a fold"
            )
        yield from super().split(X, y, np.asarray(groups))


def make_cv_splitter(n_splits: int = 5, seed: int = 0) -> PatientGroupedKFold:
    return PatientGroupedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
