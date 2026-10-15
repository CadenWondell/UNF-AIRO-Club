"""T124: the index-visit-bias check and ADR-002 matched control sampling."""

from __future__ import annotations

from pathlib import Path

import pytest

from clinical_ml_kits import load_kit
from clinical_ml_kits.leakage.visit_bias import check_visit_bias

FIX = Path(__file__).resolve().parents[1] / "fixtures"
BIASED = FIX / "kits" / "visit_bias" / "kit_visit_bias.yaml"
TOY = FIX / "kits" / "toy_binary"


@pytest.fixture(scope="module")
def biased():  # type: ignore[no-untyped-def]
    kit = load_kit(BIASED)
    with pytest.warns(UserWarning, match="index-visit bias"):
        data = kit.load()
    return kit, data


def test_utilization_only_signal_is_reported(biased) -> None:  # type: ignore[no-untyped-def]
    kit, data = biased
    report = data.visit_bias
    assert report is not None and report.exceeded
    assert report.auroc > kit.definition.visit_bias_check.max_utilization_auroc
    assert report.features == ["fx_outpatient_visits__count"]


def test_function_reports_without_signal(toy_kit, toy_data) -> None:  # type: ignore[no-untyped-def]
    r = check_visit_bias(toy_data, ["fx_outpatient_visits__count"], bound=0.99)
    assert 0.0 <= r.auroc <= 1.0 and not r.exceeded


def test_matched_controls_share_visit_type_and_year(biased) -> None:  # type: ignore[no-untyped-def]
    kit, _ = biased
    from clinical_ml_kits.cohort.labels import build_cohort

    t = build_cohort(kit.phenotype, kit.definition.cohort, kit.adapter).table.set_index("person_id")
    ctrl = t[t.label == 0]
    assert len(ctrl) > 50
    for pid, row in ctrl.iterrows():
        case = t.loc[row.matched_case]
        assert (row.visit_type, row.calendar_year) == (case.visit_type, case.calendar_year), pid


def test_schema_rejects_unknown_utilization_feature(tmp_path: Path) -> None:
    from clinical_ml_kits.core.errors import KitValidationError
    from clinical_ml_kits.core.kit_schema import (
        ValidationContext,
        load_kit_definition,
        validate_kit,
    )

    text = BIASED.read_text().replace("[fx_outpatient_visits]", "[no_such_feature]")
    p = FIX / "kits" / "visit_bias" / "_tmp_bad.yaml"
    p.write_text(text)
    try:
        with pytest.raises(KitValidationError, match="visit_bias_check"):
            validate_kit(load_kit_definition(p), "schema", ValidationContext.from_root(FIX))
    finally:
        p.unlink()
