"""Template A notebook values: rendered literally from kit.yaml and KitDocs (plan § 10)."""

from __future__ import annotations

import re
from typing import Any

from clinical_ml_kits.core.kit_schema import LoadedKit, _states
from clinical_ml_kits.core.values import PROVISIONAL_BANNER, Provisional, resolve
from clinical_ml_kits.notebooks.render import pyrepr


def _doc(kit: LoadedKit, name: str) -> str:
    p = kit.kit_dir / kit.definition.docs / name
    if not p.is_file():
        return ""
    text = p.read_text()
    text = re.sub(r"^# .*\n+", "", text, count=1)  # drop the file title
    return re.sub(r"^(#+) ", lambda m: "##" + m.group(1) + " ", text, flags=re.M).strip()


def _baseline_params(kit: LoadedKit) -> str:
    p = kit.definition.baseline.params
    return ", ".join(
        [
            f"C={p.C!r}",
            f"penalty={pyrepr(p.penalty)}",
            f"class_weight={pyrepr(p.class_weight)}",
            f"max_iter={p.max_iter}",
            f"solver={pyrepr(p.solver)}",
        ]
    )


def notebook_values(kit: LoadedKit, ctx: Any) -> dict[str, str]:
    d, ph = kit.definition, kit.phenotype
    reg = ctx.registry
    prov = [(path, v) for path, v in _states(kit) if isinstance(v, Provisional)]
    if prov:
        rows = "\n".join(f"| `{p}` | `{v.provisional}` | pending {v.pending} |" for p, v in prov)
        provisional_md = (
            f"> **{PROVISIONAL_BANNER}**\n>\n> The values below exist only so the "
            "kit runs on synthetic data. They are not approved clinical rules.\n\n"
            "| Item | Provisional value | Verification |\n|---|---|---|\n" + rows
        )
    else:
        provisional_md = "All clinical values in this kit are verified."
    feat_rows = "\n".join(
        f"| `{f.feature}` | {reg.get(f.feature).description} | {', '.join(f.derivations)}"
        f"{' (window ' + f.window + ')' if f.window else ''} |"
        for f in d.features
    )
    excl = [f"- `{c}` — label-defining concept" for c in ph.label_defining_concepts]
    excl += [f"- `{p.feature or p.concept or p.domain}` — {p.reason}" for p in d.prohibited]
    numeric_measurements = [
        f"{f.feature}__{f.derivations[0]}"
        for f in d.features
        if reg.get(f.feature).domain == "measurement"
    ][:3]
    cs = ph.control_sampling
    ratio = f", {resolve(cs.controls_per_case)} controls per case" if cs.controls_per_case else ""
    method = d.calibration.method.split("_")[-1] if d.calibration.method != "none" else "sigmoid"
    metrics = [m for m in d.metrics if m != "confusion_matrix"]
    return {
        "question": f"**Clinical question.** {d.clinical_question.strip()}",
        "background_md": _doc(kit, "clinical_background.md"),
        "construction_md": _doc(kit, "construction.md"),
        "limitations_md": _doc(kit, "limitations.md"),
        "provisional_md": provisional_md,
        "features_md": "| Feature | Meaning | Derivations |\n|---|---|---|\n" + feat_rows,
        "excluded_md": "\n".join(excl),
        "sampling_md": f"strategy `{cs.strategy}`{ratio}",
        "baseline_params": _baseline_params(kit),
        "threshold_rule": d.threshold_rule,
        "threshold_rule_literal": pyrepr(d.threshold_rule),
        "metrics_literal": pyrepr(metrics),
        "calibration_bins": str(d.calibration.bins),
        "calibration_strategy": pyrepr(d.calibration.strategy),
        "calibration_method": pyrepr(method),
        "seed": str(d.seed),
        "eda_columns": pyrepr(numeric_measurements),
        "demo_model_file": pyrepr(f"{d.kit_id}_demo_model.joblib"),
        "prediction_type": d.prediction_type,
        "template_family": d.template_family,
    }
