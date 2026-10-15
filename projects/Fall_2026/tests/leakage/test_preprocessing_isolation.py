"""T098: preprocessing learned from training rows only; explicit missingness."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer

from clinical_ml_kits.preprocessing import make_preprocessor


def _num(pre):  # type: ignore[no-untyped-def]
    return pre.named_transformers_["numeric"]


def test_statistics_equal_train_only(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    pre = make_preprocessor(toy_kit.feature_spec).fit(toy_data.train.X)
    num_cols = list(toy_kit.feature_spec.numeric)
    Xn = toy_data.train.X[num_cols].astype(float)
    imp: SimpleImputer = _num(pre).named_steps["impute"]
    keep = Xn.notna().any().to_numpy()
    np.testing.assert_allclose(imp.statistics_[keep], Xn.median()[keep].to_numpy())
    imputed = Xn.fillna(Xn.median())
    sc = _num(pre).named_steps["scale"]
    np.testing.assert_allclose(sc.mean_[: keep.sum()], imputed.loc[:, keep].mean().to_numpy())


def test_perturbing_validation_leaves_fit_unchanged(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    a = make_preprocessor(toy_kit.feature_spec).fit(toy_data.train.X)
    b = make_preprocessor(toy_kit.feature_spec).fit(toy_data.train.X)
    noisy = toy_data.validation.X.copy()
    num = list(toy_kit.feature_spec.numeric)
    noisy[num] = noisy[num] * 1000 + 7
    b.transform(noisy)
    np.testing.assert_allclose(
        _num(a).named_steps["scale"].mean_, _num(b).named_steps["scale"].mean_
    )
    np.testing.assert_allclose(
        _num(a).named_steps["impute"].statistics_, _num(b).named_steps["impute"].statistics_
    )


def test_feature_order_names_and_indicators(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    pre = make_preprocessor(toy_kit.feature_spec).fit(toy_data.train.X)
    names = list(pre.get_feature_names_out())
    num = [c for c in toy_kit.feature_spec.numeric if toy_data.train.X[c].notna().any()]
    assert names[: len(num)] == num
    missing = [c for c in num if toy_data.train.X[c].isna().any()]
    assert missing and all(f"missingindicator_{c}" in names for c in missing)


def test_numeric_nan_not_replaced_by_constant() -> None:
    from clinical_ml_kits.core.kit import FeatureSpec

    spec = FeatureSpec(numeric=("lab__latest",), categorical=("sex__latest",))
    X = pd.DataFrame({"lab__latest": [1.0, 3.0, np.nan, 5.0], "sex__latest": ["F", None, "M", "F"]})
    pre = make_preprocessor(spec).fit(X)
    imp = pre.named_transformers_["numeric"].named_steps["impute"]
    assert imp.strategy == "median" and imp.add_indicator
    out = pd.DataFrame(pre.transform(X), columns=pre.get_feature_names_out())
    ind = out["missingindicator_lab__latest"]  # standardized by the scaler (plan § 16)
    assert ind.nunique() == 2 and ind.idxmax() == 2 and (ind.drop(2) == ind.iloc[0]).all()
    cat = pre.named_transformers_["categorical"]
    assert cat.named_steps["impute"].fill_value == "__missing__"
    assert "sex__latest___missing__" in out.columns
