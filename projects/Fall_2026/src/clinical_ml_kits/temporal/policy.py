"""Resolved temporal policy: concrete values from a kit's TemporalPolicy value states."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from clinical_ml_kits.core.values import parse_duration, resolve


@dataclass(frozen=True)
class WindowedExclusion:
    concept: str | None
    domain: str | None
    before: timedelta
    after: timedelta
    reason: str = ""


@dataclass(frozen=True)
class ResolvedTemporalPolicy:
    """Concrete temporal policy. Index times are date precision (M1–4 kits).

    An observation is permitted only if (data-model § 2):
    1. upper bound: ``include``: date(o) <= date(index) - washout;
       ``exclude_index_day``: date(o) < date(index) - washout (date-only rows on the index day
       are same-day);
    2. date(o) >= date(index) - lookback;
    3. if ``exclude_index_encounter``: o.visit_id != index_visit_id;
    4. o is not inside any windowed exclusion [date(index) - before, date(index) + after] that
       matches its logical concept or domain.
    (Rule 5, label-defining concepts, is enforced separately at all times.)
    """

    same_day: str
    washout: timedelta
    lookback: timedelta
    exclude_index_encounter: bool
    windowed_exclusions: tuple[WindowedExclusion, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.same_day not in ("include", "exclude_index_day"):
            raise ValueError(
                f"same_day must be include or exclude_index_day, not {self.same_day!r}"
            )
        if self.washout < timedelta(0) or self.lookback <= timedelta(0):
            raise ValueError("washout must be >= 0 and lookback > 0")

    @classmethod
    def from_values(
        cls,
        *,
        same_day: str,
        washout: str,
        lookback: str,
        exclude_index_encounter: bool,
        windowed_exclusions: list[dict[str, Any]] | None = None,
    ) -> ResolvedTemporalPolicy:
        wins = tuple(
            WindowedExclusion(
                concept=w.get("concept"),
                domain=w.get("domain"),
                before=parse_duration(w["before"]),
                after=parse_duration(w["after"]),
                reason=w.get("reason", ""),
            )
            for w in (windowed_exclusions or [])
        )
        return cls(
            same_day,
            parse_duration(washout),
            parse_duration(lookback),
            bool(exclude_index_encounter),
            wins,
        )

    @classmethod
    def from_schema(cls, tp: Any) -> ResolvedTemporalPolicy:
        """From a kit TemporalPolicy; UNVERIFIED values raise (synthetic level forbids them)."""
        wins = [
            {
                "concept": w.target.concept,
                "domain": w.target.domain,
                "before": resolve(w.before),
                "after": resolve(w.after),
                "reason": w.reason,
            }
            for w in tp.windowed_exclusions
        ]
        return cls.from_values(
            same_day=resolve(tp.same_day),
            washout=resolve(tp.washout),
            lookback=resolve(tp.lookback),
            exclude_index_encounter=resolve(tp.exclude_index_encounter),
            windowed_exclusions=wins,
        )
