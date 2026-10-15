"""Template A preprocessing factory (plan § 16). Fitted inside a Pipeline on training rows only."""

from __future__ import annotations

from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler


def _none_to_nan(X: Any) -> Any:
    """Treat ``None`` as missing in categorical columns (older pandas/scikit-learn do not)."""
    import numpy as np
    import pandas as pd

    df = pd.DataFrame(X)
    return df.astype(object).where(df.notna(), np.nan)


def make_preprocessor(feature_spec: Any) -> ColumnTransformer:
    """Numeric: median imputation + missingness indicators → standard scaling.
    Categorical: constant ``"__missing__"`` → one-hot (unknown categories ignored).

    Missing numeric values are never treated as a "normal" constant; indicators keep
    missingness visible to the model (FR-059).
    """
    transformers: list[tuple[str, Any, list[str]]] = []
    if feature_spec.numeric:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                        ("scale", StandardScaler()),
                    ]
                ),
                list(feature_spec.numeric),
            )
        )
    if feature_spec.categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "as_missing",
                            FunctionTransformer(_none_to_nan, feature_names_out="one-to-one"),
                        ),
                        ("impute", SimpleImputer(strategy="constant", fill_value="__missing__")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                list(feature_spec.categorical),
            )
        )
    return ColumnTransformer(transformers, verbose_feature_names_out=False)
