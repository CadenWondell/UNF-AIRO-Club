"""Clinical value states (contracts/kit-definition.md): verified, provisional, unverified.

YAML forms:

- verified:     ``{value: <v>, provenance: [<ProvenanceRef with verification_status: verified>]}``
- provisional:  ``{provisional: <v>, note: "...", pending: V-xx}`` (synthetic execution only)
- unverified:   ``UNVERIFIED``
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import timedelta
from typing import TYPE_CHECKING, Annotated, Any, Generic, TypeVar, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
    model_validator,
)

from clinical_ml_kits.provenance.models import ProvenanceRef

T = TypeVar("T")

UNVERIFIED = "UNVERIFIED"
PENDING_PATTERN = r"^V-\d{2}[a-z]?(/V-\d{2}[a-z]?)*$"
PROVISIONAL_BANNER = "PROVISIONAL — synthetic-only, not an approved clinical definition"

DURATION_PATTERN = r"^P(\d+)([DW])$"
Duration = Annotated[str, Field(pattern=DURATION_PATTERN)]


def parse_duration(value: str) -> timedelta:
    """Parse the restricted ISO-8601 durations used in kits (``PnD`` or ``PnW`` only).

    Years and months are rejected on purpose: their length in days is ambiguous.
    """
    m = re.match(DURATION_PATTERN, value)
    if not m:
        raise ValueError(f"unsupported duration {value!r}; use PnD or PnW")
    n = int(m.group(1))
    return timedelta(days=n if m.group(2) == "D" else 7 * n)


class Unverified(BaseModel):
    """The ``UNVERIFIED`` sentinel: no value yet (schema level only)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="before")
    @classmethod
    def _from_sentinel(cls, data: Any) -> Any:
        if data == UNVERIFIED:
            return {}
        raise ValueError(f"expected the {UNVERIFIED} sentinel")

    @model_serializer
    def _ser(self) -> str:
        return UNVERIFIED

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: Any, handler: Any) -> dict[str, Any]:
        return {"const": UNVERIFIED, "type": "string", "title": "Unverified sentinel"}

    state: str = Field(default="unverified", exclude=True)


class Provisional(BaseModel, Generic[T]):
    """A concrete value for synthetic execution and tests only; never an approved clinical rule."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provisional: T
    note: str = Field(min_length=1)
    pending: str = Field(pattern=PENDING_PATTERN)
    provenance: list[ProvenanceRef] = Field(default_factory=list)

    @field_validator("note")
    @classmethod
    def _note_disclaims(cls, v: str) -> str:
        low = v.lower()
        if "synthetic" not in low or "not an approved" not in low:
            raise ValueError(
                "note must state the value is for synthetic execution/testing and is "
                "not an approved clinical rule"
            )
        return v

    @property
    def value(self) -> T:
        return self.provisional


class Sourced(BaseModel, Generic[T]):
    """A verified value: at least one inline ProvenanceRef has ``verification_status: verified``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: T
    provenance: list[ProvenanceRef] = Field(min_length=1)

    @model_validator(mode="after")
    def _needs_verified_ref(self) -> Sourced[T]:
        if not any(r.is_verified for r in self.provenance):
            raise ValueError(
                "a sourced value needs a verified ProvenanceRef; "
                "use {provisional, note, pending} or UNVERIFIED instead"
            )
        return self


if TYPE_CHECKING:
    ClinicalValue = Union[Sourced[T], Provisional[T], Unverified]
else:

    class ClinicalValue:
        """``ClinicalValue[X]`` = ``Sourced[X] | Provisional[X] | Unverified``."""

        def __class_getitem__(cls, item: Any) -> Any:
            return Union[Sourced[item], Provisional[item], Unverified]


def state_of(v: object) -> str | None:
    if isinstance(v, Sourced):
        return "verified"
    if isinstance(v, Provisional):
        return "provisional"
    if isinstance(v, Unverified):
        return "unverified"
    return None


def resolve(v: object) -> Any:
    """Concrete value of a clinical value (verified or provisional). Raises on UNVERIFIED."""
    if isinstance(v, (Sourced, Provisional)):
        return v.value
    if isinstance(v, Unverified):
        raise ValueError("UNVERIFIED value cannot be used for execution")
    return v


def iter_value_states(obj: object, path: str = "") -> Iterator[tuple[str, object]]:
    """Yield ``(dotted.path, value_state_object)`` for every clinical value in a model tree."""
    if state_of(obj) is not None:
        yield path, obj
        return
    if isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            yield from iter_value_states(getattr(obj, name), f"{path}.{name}" if path else name)
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            yield from iter_value_states(item, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for k, item in obj.items():
            yield from iter_value_states(item, f"{path}.{k}" if path else str(k))


def iter_provenance(obj: object, path: str = "") -> Iterator[tuple[str, ProvenanceRef]]:
    """Yield every inline ProvenanceRef in a model tree."""
    if isinstance(obj, ProvenanceRef):
        yield path, obj
    elif isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            yield from iter_provenance(getattr(obj, name), f"{path}.{name}" if path else name)
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            yield from iter_provenance(item, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for k, item in obj.items():
            yield from iter_provenance(item, f"{path}.{k}" if path else str(k))
