"""Leakage checks (constitution VI; SC-005). Each failure raises a named LeakageError subclass."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pandas as pd

from clinical_ml_kits.core.errors import (
    LabelLeakageError,
    PatientLeakageError,
    PreprocessingLeakageError,
    ProhibitedFeatureError,
    SameDayLeakageError,
    TargetLeakageError,
    TemporalLeakageError,
)
from clinical_ml_kits.temporal.cutoff import effective_upper_bound
from clinical_ml_kits.temporal.policy import ResolvedTemporalPolicy


def check_patients(partitions: Mapping[str, set[str]]) -> None:
    """No person may appear in more than one partition."""
    names = sorted(partitions)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            both = partitions[a] & partitions[b]
            if both:
                raise PatientLeakageError(
                    f"{len(both)} person(s) in both {a} and {b}: {sorted(both)[:3]}"
                )


def check_lineage(
    lineage: pd.DataFrame, cohort: pd.DataFrame, policy: ResolvedTemporalPolicy
) -> None:
    """Every feature's latest source observation is permitted for its row's index."""
    if lineage.empty:
        return
    m = lineage.merge(cohort, on="person_id", how="left")
    if m.index_time.isna().any():
        raise TemporalLeakageError("lineage rows for persons without an index time")
    bound = m.index_time.map(lambda t: effective_upper_bound(t, policy))
    late = m[m.max_source_time >= bound]
    if len(late):
        idx_day = late.index_time.dt.normalize()
        src_day = late.max_source_time.dt.normalize()
        if (src_day > idx_day).any() or policy.same_day == "include":
            raise TemporalLeakageError(
                f"{len(late)} feature value(s) use observations after the effective cutoff "
                f"(e.g. {late.feature.iloc[0]})"
            )
        raise SameDayLeakageError(
            f"{len(late)} feature value(s) use index-day observations under exclude_index_day"
        )
    if policy.exclude_index_encounter and "index_visit_id" in m:
        enc = m[m.visit_id.notna() & (m.visit_id == m.index_visit_id)]
        if len(enc):
            raise SameDayLeakageError(
                f"{len(enc)} feature value(s) come from the index encounter "
                f"(e.g. {enc.feature.iloc[0]})"
            )


def check_target_overlap(
    feature_concepts: Mapping[str, str], label_defining: Iterable[str], justified: set[str]
) -> None:
    """Model inputs must not use label-defining (target-defining) logical concepts."""
    bad = sorted(
        f for f, c in feature_concepts.items() if c in set(label_defining) and f not in justified
    )
    if bad:
        raise TargetLeakageError(f"features use label-defining concepts: {bad}")


def check_label_sources(
    feature_concepts: Mapping[str, str],
    label_source_concepts: Iterable[str],
    justified: set[str] = frozenset(),  # type: ignore[assignment]
) -> None:
    """Concepts used by the case/control rules must not be predictors (even if undeclared)."""
    src = set(label_source_concepts)
    bad = sorted(
        f"{f} ({c})" for f, c in feature_concepts.items() if c in src and f not in justified
    )
    if bad:
        raise LabelLeakageError(f"label-source observations used as features: {bad}")


def check_prohibited(
    features: Mapping[str, tuple[str, str]],
    prohibited: Iterable[Mapping[str, Any]],
    justified: set[str],
) -> None:
    """``features``: name -> (concept, domain); prohibited items by feature, concept, or domain."""
    items = list(prohibited)
    for name, (concept, domain) in features.items():
        if name in justified:
            continue
        for p in items:
            if p.get("feature") == name or p.get("concept") == concept or p.get("domain") == domain:
                raise ProhibitedFeatureError(
                    f"feature {name!r} is prohibited ({p}) and has no justified inclusion"
                )


def _fitted_steps(model: Any, top: bool = True) -> list[tuple[str, Any]]:
    """Every preprocessing step: all top-level steps but the estimator, recursing into
    ColumnTransformers and nested Pipelines (whose steps are all preprocessing)."""
    steps = getattr(model, "steps", None)
    if steps is None:
        return []
    out: list[tuple[str, Any]] = []
    for name, step in steps[:-1] if top else steps:
        out.append((name, step))
        for sub in getattr(step, "transformers_", []) or []:
            out.append((f"{name}.{sub[0]}", sub[1]))
            out += [(f"{name}.{sub[0]}.{n}", s) for n, s in _fitted_steps(sub[1], top=False)]
        out += [(f"{name}.{n}", s) for n, s in _fitted_steps(step, top=False)]
    return out


def check_preprocessing_fit(model: Any, n_train: int) -> None:
    """Every fitted preprocessing step must have seen exactly the training rows."""
    for name, step in _fitted_steps(model):
        n = getattr(step, "n_samples_seen_", None)
        if n is None:
            continue
        seen = int(n.max()) if hasattr(n, "max") else int(n)
        if seen != n_train:
            raise PreprocessingLeakageError(
                f"preprocessing step {name!r} was fitted on {seen} rows, but the training "
                f"partition has {n_train}"
            )
