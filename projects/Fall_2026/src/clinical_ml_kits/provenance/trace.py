"""Feature traceability (FR-153, P-8): feature → logical concept → realization → table → source."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clinical_ml_kits.core.errors import PendingVerification

# Source table per domain for the OMOP namespace (OMOP CDM v5.4 table names, tier 3); the
# synthetic namespace serves every domain from its generated observation table.
OMOP_TABLES = {
    "person": "person",
    "measurement": "measurement",
    "condition": "condition_occurrence",
    "drug": "drug_exposure",
    "procedure": "procedure_occurrence",
    "visit": "visit_occurrence",
    "observation": "observation",
    "device": "device_exposure",
    "survey": "observation",
}


class TraceError(LookupError):
    def __init__(self, link: str, detail: str) -> None:
        self.link = link
        super().__init__(f"traceability broken at {link}: {detail}")


@dataclass(frozen=True)
class TraceChain:
    feature_key: str
    logical_id: str
    concept_sources: tuple[str, ...]
    namespace: str
    realization_version: str
    mapping_sources: tuple[str, ...]
    domain: str
    source_table: str


def trace_feature(feature_key: str, namespace: str, ctx: Any) -> TraceChain:
    """Resolve the full chain for one feature; raises TraceError naming the broken link."""
    try:
        entry = ctx.registry.get(feature_key)
    except KeyError as e:
        raise TraceError("feature", str(e)) from None
    try:
        concept = ctx.concepts.concept(entry.concept.id)
    except KeyError as e:
        raise TraceError("logical_concept", str(e)) from None
    if concept.domain != entry.domain:
        raise TraceError("logical_concept", f"domain {concept.domain} != feature {entry.domain}")
    if not concept.provenance:
        raise TraceError("logical_concept", "no clinical-meaning provenance")
    try:
        real = ctx.concepts.realization(namespace, concept.logical_id)
    except PendingVerification as e:
        raise TraceError("realization", str(e)) from None
    if real.domain != concept.domain:
        raise TraceError("realization", f"domain {real.domain} != concept {concept.domain}")
    for link, refs in (("concept_source", concept.provenance), ("mapping_source", real.provenance)):
        for ref in refs:
            if ctx.source(ref.source_id) is None:
                raise TraceError(link, f"source {ref.source_id!r} has no SourceRecord")
    table = OMOP_TABLES[real.domain] if namespace == "omop" else "synthetic_observations"
    return TraceChain(
        feature_key=feature_key,
        logical_id=concept.logical_id,
        concept_sources=tuple(r.source_id for r in concept.provenance),
        namespace=namespace,
        realization_version=real.version,
        mapping_sources=tuple(r.source_id for r in real.provenance),
        domain=real.domain,
        source_table=table,
    )
