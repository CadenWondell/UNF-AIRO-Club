"""T114: V-03 dissemination filter on outputs leaving the Workbench (synthetic counts only)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from clinical_ml_kits.completion.suppression import (
    filter_for_export,
    suppress_bins,
    suppress_confusion,
    suppress_count,
    suppress_metrics,
)
from clinical_ml_kits.core.errors import PendingVerification
from clinical_ml_kits.data.policy import policy_for

ROOT = Path(__file__).resolve().parents[3]
RULE = policy_for("all_of_us_workbench").dissemination_rule(ROOT / "definitions")


def test_rule_comes_from_v03_record() -> None:
    rec = yaml.safe_load((ROOT / "definitions/sources/aou_dissemination_policy.yaml").read_text())
    assert (RULE.suppress_min, RULE.suppress_max) == (
        rec["parameters"]["suppress_min"],
        rec["parameters"]["suppress_max"],
    )


@pytest.mark.parametrize("n,expected", [(0, 0), (1, "<=20"), (20, "<=20"), (21, 21), (500, 500)])
def test_counts(n: int, expected: object) -> None:
    assert suppress_count(n, RULE) == expected


def test_confusion_complementary_suppression() -> None:
    cm = suppress_confusion({"tn": 400, "fp": 30, "fn": 5, "tp": 60}, RULE)
    assert cm["fn"] == "<=20"
    assert sum(v == "<=20" for v in cm.values()) >= 2  # fn could otherwise be derived from totals
    assert suppress_confusion({"tn": 400, "fp": 30, "fn": 25, "tp": 60}, RULE) == {
        "tn": 400,
        "fp": 30,
        "fn": 25,
        "tp": 60,
    }


def test_calibration_bins() -> None:
    b = pd.DataFrame(
        {"bin": [0, 1], "n": [5, 300], "mean_predicted": [0.1, 0.5], "observed_rate": [0.2, 0.48]}
    )
    out = suppress_bins(b, RULE, n_events=pd.Series([1, 144]))
    assert out.loc[0, "n"] == "<=20" and pd.isna(out.loc[0, "observed_rate"])
    assert out.loc[1, "n"] == 300 and out.loc[1, "observed_rate"] == 0.48


def test_derived_metrics_suppressed_for_small_groups() -> None:
    m = {"auroc": 0.8, "auprc": 0.5, "sensitivity": 0.7, "prevalence": 0.05}
    assert suppress_metrics(m, n_pos=12, n_neg=500, rule=RULE) == {
        k: "<=20 (suppressed)" for k in m
    }
    assert suppress_metrics(m, n_pos=40, n_neg=500, rule=RULE) == m


def test_subgroup_table_and_descriptive_stats() -> None:
    t = pd.DataFrame({"subgroup": ["a", "b"], "n": [15, 120], "n_pos": [3, 40]})
    out = filter_for_export(
        {"subgroups": t.to_dict("records"), "eligible_persons": 19, "positives": 0}, RULE
    )
    assert out["subgroups"][0]["n"] == "<=20" and out["subgroups"][0]["n_pos"] == "<=20"
    assert out["subgroups"][1] == {"subgroup": "b", "n": 120, "n_pos": 40}
    assert out["eligible_persons"] == "<=20" and out["positives"] == 0


def test_synthetic_exports_unfiltered() -> None:
    assert policy_for("synthetic").dissemination_rule(ROOT / "definitions") is None


def test_unresolved_v03_blocks_workbench_export(tmp_path: Path) -> None:
    (tmp_path / "sources").mkdir()
    with pytest.raises(PendingVerification):
        policy_for("all_of_us_workbench").dissemination_rule(tmp_path)
