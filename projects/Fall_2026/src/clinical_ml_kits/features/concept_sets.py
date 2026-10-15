"""Logical concepts and per-namespace concept-set realizations (data-model § 2, R-24).

Kits reference logical concept ids. Each adapter resolves them through its own namespace
(``omop`` → verified realizations only; ``synthetic`` → fictional ``SYN-`` codes).
"""

from __future__ import annotations

import re
from functools import cached_property
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from clinical_ml_kits.core.errors import PendingVerification
from clinical_ml_kits.provenance.models import ProvenanceRef

Domain = Literal[
    "person",
    "measurement",
    "condition",
    "drug",
    "procedure",
    "visit",
    "observation",
    "survey",
    "device",
]
Namespace = Literal["omop", "synthetic"]
LOGICAL_ID = r"^[a-z][a-z0-9_]*$"
SYNTHETIC_HEADER = "synthetic; not real OMOP concepts"
SEMVER = r"^\d+\.\d+\.\d+$"


class LogicalConceptRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=LOGICAL_ID)
    version: str = Field(pattern=SEMVER)


class LogicalConcept(BaseModel):
    """Data-source-independent clinical meaning (clinical-meaning provenance)."""

    model_config = ConfigDict(extra="forbid")
    logical_id: str = Field(pattern=LOGICAL_ID)
    version: str = Field(pattern=SEMVER)
    status: Literal["draft", "requires_verification", "verified", "approved"]
    description: str = Field(min_length=1)
    domain: Domain
    provenance: list[ProvenanceRef] = Field(min_length=1)
    notes: str = ""


class Member(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    concept_id: str = Field(min_length=1)
    include_descendants: bool = False
    exclude: bool = False


class AcceptedUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    unit: str
    factor_to_canonical: float


class ConceptSetRealization(BaseModel):
    """A dataset-specific realization of one logical concept (mapping provenance)."""

    model_config = ConfigDict(extra="forbid")
    header: str | None = None
    logical_id: str = Field(pattern=LOGICAL_ID)
    version: str = Field(pattern=SEMVER)
    namespace: Namespace
    status: Literal["draft", "requires_verification", "verified", "approved"]
    domain: Domain
    vocabulary: str
    members: list[Member] = Field(default_factory=list)
    accepted_units: list[AcceptedUnit] = Field(default_factory=list)
    canonical_unit: str | None = None
    provenance: list[ProvenanceRef] = Field(min_length=1)
    notes: str = ""

    @model_validator(mode="after")
    def _namespace_rules(self) -> ConceptSetRealization:
        if self.namespace == "synthetic":
            if self.header != SYNTHETIC_HEADER:
                raise ValueError(f"synthetic realizations must carry header {SYNTHETIC_HEADER!r}")
            bad = [m.concept_id for m in self.members if not re.match(r"^SYN-", m.concept_id)]
            if bad:
                raise ValueError(f"synthetic members must use SYN- codes: {bad}")
        return self

    @property
    def mapping_verified(self) -> bool:
        return any(r.is_verified for r in self.provenance)

    @property
    def codes(self) -> list[str]:
        return [m.concept_id for m in self.members if not m.exclude]

    def unit_factor(self, unit: str | None) -> float | None:
        """Conversion factor to the canonical unit, or None if the unit is not accepted."""
        if not self.accepted_units:
            return 1.0
        for u in self.accepted_units:
            if u.unit == unit:
                return u.factor_to_canonical
        return None


def _semver_key(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


class ConceptRepository:
    """Loads ``definitions/concepts`` and ``definitions/concept_sets/<namespace>``."""

    def __init__(self, definitions_dir: Path) -> None:
        self.root = Path(definitions_dir)

    @cached_property
    def concepts(self) -> dict[str, LogicalConcept]:
        out: dict[str, LogicalConcept] = {}
        for p in sorted((self.root / "concepts").glob("*.yaml")):
            c = LogicalConcept.model_validate(yaml.safe_load(p.read_text()))
            if c.logical_id != p.stem:
                raise ValueError(f"{p}: logical_id {c.logical_id!r} must match the file name")
            out[c.logical_id] = c
        return out

    @cached_property
    def realizations(self) -> dict[tuple[str, str], dict[str, ConceptSetRealization]]:
        """{(namespace, logical_id): {version: realization}}."""
        out: dict[tuple[str, str], dict[str, ConceptSetRealization]] = {}
        base = self.root / "concept_sets"
        for p in sorted(base.glob("*/*/*.yaml")):
            namespace, logical_id, version = p.parent.parent.name, p.parent.name, p.stem
            r = ConceptSetRealization.model_validate(yaml.safe_load(p.read_text()))
            if (r.namespace, r.logical_id, r.version) != (namespace, logical_id, version):
                raise ValueError(f"{p}: namespace/logical_id/version must match its path")
            out.setdefault((namespace, logical_id), {})[version] = r
        return out

    def concept(self, logical_id: str) -> LogicalConcept:
        try:
            return self.concepts[logical_id]
        except KeyError:
            raise KeyError(f"unknown logical concept {logical_id!r}") from None

    def realization(
        self, namespace: str, logical_id: str, version: str | None = None
    ) -> ConceptSetRealization:
        """Resolve a realization; latest version when ``version`` is None.

        Raises PendingVerification when it is missing, or (``omop``) when its mapping is not
        verified. Never resolves another namespace.
        """
        versions = self.realizations.get((namespace, logical_id))
        if not versions:
            raise PendingVerification(
                "V-25" if namespace == "omop" else "realization",
                f"no {namespace} realization for logical concept {logical_id!r}",
            )
        key = version or max(versions, key=_semver_key)
        if key not in versions:
            raise PendingVerification("realization", f"{namespace}/{logical_id}@{key} missing")
        r = versions[key]
        concept = self.concepts.get(logical_id)
        if concept is None:
            raise KeyError(f"realization {namespace}/{logical_id} has no logical concept")
        if r.domain != concept.domain:
            raise ValueError(
                f"{namespace}/{logical_id}@{key}: domain {r.domain} != logical concept domain "
                f"{concept.domain}"
            )
        if namespace == "omop" and not (r.mapping_verified and (r.members or r.domain == "person")):
            raise PendingVerification(
                "V-25", f"omop realization {logical_id}@{key} is not verified"
            )
        return r
