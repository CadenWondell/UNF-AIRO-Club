"""Automated provenance checks P-1…P-11 (contracts/provenance.md)."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from clinical_ml_kits.core.errors import KitValidationError
from clinical_ml_kits.provenance.hashing import content_hash, iter_owned_refs

Severity = Literal["error", "warning"]
STATUS_KEYS = frozenset({"status", "verification_status", "state", "verified", "approved"})


@dataclass(frozen=True)
class Finding:
    check_id: str
    severity: Severity
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.check_id} [{self.severity}] {self.path}: {self.message}"


def _walk(obj: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def _generic(doc: Any, ctx: Any, where: str) -> list[Finding]:
    out: list[Finding] = []
    for owner, ref, path in iter_owned_refs(doc):
        p = f"{where}:{path}"
        if ctx is not None and ctx.source(ref["source_id"]) is None:
            out.append(Finding("P-1", "error", p, f"source_id {ref['source_id']!r} unresolved"))
        if ref.get("verification_status") == "verified":
            if not ref.get("verified_by") or not ref.get("verified_on"):
                out.append(Finding("P-3", "error", p, "verified ref lacks verified_by/verified_on"))
            stored = ref.get("content_hash")
            if not stored:
                out.append(
                    Finding("P-7", "error", p, "verified item lacks content_hash (run stamp)")
                )
            elif stored != content_hash(owner):
                out.append(
                    Finding(
                        "P-7",
                        "error",
                        p,
                        "item edited since verification: content hash changed; status must "
                        "revert to requires_verification",
                    )
                )
    for path, node in _walk(doc):
        if isinstance(node, dict) and "provisional" in node:
            missing = [k for k in ("note", "pending") if not node.get(k)]
            if missing:
                out.append(
                    Finding(
                        "P-10", "error", f"{where}:{path}", f"provisional value lacks {missing}"
                    )
                )
        if isinstance(node, dict) and "deviations" in node and isinstance(node["deviations"], list):
            need = ("item", "official_definition", "deviation", "reason", "expected_impact")
            for i, dev in enumerate(node["deviations"]):
                missing = [k for k in need if not (isinstance(dev, dict) and dev.get(k))]
                if missing:
                    out.append(
                        Finding(
                            "P-6",
                            "error",
                            f"{where}:{path}.deviations[{i}]",
                            f"deviation lacks {missing}",
                        )
                    )
    return out


def _needs_provenance(doc: dict[str, Any], key: str, where: str) -> list[Finding]:
    if not doc.get(key):
        return [Finding("P-2", "error", f"{where}:{key}", "required item has no provenance")]
    return []


def check_document(kind: str, doc: Any, ctx: Any = None, where: str = "") -> list[Finding]:
    """Run P-checks on one definition document of ``kind``."""
    where = where or kind
    out = _generic(doc, ctx, where)
    if kind == "concept":
        out += _needs_provenance(doc, "provenance", where)
    elif kind == "realization":
        out += _needs_provenance(doc, "provenance", where)
        refs = doc.get("provenance") or []
        verified = any(r.get("verification_status") == "verified" for r in refs)
        members = doc.get("members") or []
        if doc.get("namespace") == "omop" and members and not verified:
            out.append(
                Finding("P-5", "error", where, "omop members present without verified mapping")
            )
        if doc.get("namespace") == "synthetic":
            bad = [
                m.get("concept_id")
                for m in members
                if not str(m.get("concept_id")).startswith("SYN-")
            ]
            if bad:
                out.append(
                    Finding("P-5", "error", where, f"synthetic members not SYN- codes: {bad}")
                )
            if doc.get("header") != "synthetic; not real OMOP concepts":
                out.append(Finding("P-5", "error", where, "synthetic header missing"))
    elif kind == "registry_entry":
        out += _needs_provenance(doc, "provenance", where)
        if ctx is not None:
            out += _trace(doc.get("feature_key", "?"), ctx, where, doc)
    elif kind == "source":
        if int(doc.get("priority_tier", 0)) >= 5 and not str(doc.get("notes", "")).strip():
            out.append(
                Finding(
                    "P-9",
                    "warning",
                    where,
                    "tier 5-6 source used without a note explaining why tiers 1-4 were "
                    "insufficient",
                )
            )
    elif kind == "verification_notes":
        for path, node in _walk(doc):
            if isinstance(node, dict):
                bad = sorted(set(node) & STATUS_KEYS)
                if bad:
                    out.append(
                        Finding(
                            "P-11",
                            "error",
                            f"{where}:{path}",
                            f"verification.yaml must not contain status fields {bad}",
                        )
                    )
            if isinstance(node, dict) and node.get("category", "documentation_derived") not in (
                "documentation_derived",
                "method_decision",
            ):
                out.append(
                    Finding(
                        "P-11", "error", f"{where}:{path}", f"bad category {node['category']!r}"
                    )
                )
    elif kind == "kit":
        for key in ("sources", "known_limitations"):
            if not doc.get(key):
                out.append(Finding("P-2", "error", f"{where}:{key}", "required item missing"))
        cohort = doc.get("cohort") or {}
        if isinstance(cohort, dict):
            out += _needs_provenance(cohort, "provenance", f"{where}:cohort")
    elif kind == "phenotype":
        out += _needs_provenance(doc, "provenance", where)
        cs = doc.get("control_sampling") or {}
        out += _needs_provenance(cs, "provenance", f"{where}:control_sampling")
    return out


def _trace(feature_key: str, ctx: Any, where: str, doc: Any = None) -> list[Finding]:
    from clinical_ml_kits.provenance.trace import TraceError, trace_feature

    if doc is not None:
        concept = (doc.get("concept") or {}).get("id")
        if concept and concept not in ctx.concepts.concepts:
            return [Finding("P-8", "error", where, f"logical concept {concept!r} not defined")]
        if feature_key not in ctx.registry:
            return []
    try:
        trace_feature(feature_key, "synthetic", ctx)
    except TraceError as e:
        return [Finding("P-8", "error", where, str(e))]
    return []


def check_kit(path: str | Path, ctx: Any) -> list[Finding]:
    """P-checks for a kit (kit.yaml + phenotype), including status gating (P-4) and P-8."""
    from clinical_ml_kits.core.kit_schema import load_kit_definition, validate_kit

    p = Path(path)
    if p.is_dir():
        p = p / "kit.yaml"
    raw = yaml.safe_load(p.read_text())
    out = check_document("kit", raw, ctx, where=str(p.name))
    try:
        kit = load_kit_definition(p)
    except KitValidationError as e:
        return [*out, Finding("schema", "error", str(p.name), str(e))]
    if not isinstance(raw.get("phenotype"), dict) or "path" in raw["phenotype"]:
        out += check_document("phenotype", kit.phenotype_raw, ctx, where="phenotype.yaml")
    else:
        out += check_document("phenotype", raw["phenotype"], ctx, where="phenotype")
    try:
        validate_kit(kit, "schema", ctx)
    except KitValidationError as e:
        for line in str(e).splitlines():
            line = line.strip()
            if not line:
                continue
            cid = "P-4" if "(P-4)" in line else "schema"
            out.append(Finding(cid, "error", kit.kit_id, line))
    for f in kit.definition.features:
        if f.feature in ctx.registry:
            out += _trace(f.feature, ctx, f"{kit.kit_id}:features.{f.feature}")
    notes = p.parent / "verification.yaml"
    if notes.is_file():
        out += check_document(
            "verification_notes", yaml.safe_load(notes.read_text()), ctx, "verification.yaml"
        )
    return out


def check_definitions(ctx: Any) -> list[Finding]:
    """P-checks over every definition file under ``ctx.definitions_dir``."""
    root = Path(ctx.definitions_dir)
    out: list[Finding] = []
    for p in sorted((root / "sources").glob("*.yaml")):
        out += check_document("source", yaml.safe_load(p.read_text()), ctx, f"sources/{p.name}")
    for p in sorted((root / "concepts").glob("*.yaml")):
        out += check_document("concept", yaml.safe_load(p.read_text()), ctx, f"concepts/{p.name}")
    for p in sorted((root / "concept_sets").glob("*/*/*.yaml")):
        rel = p.relative_to(root).as_posix()
        out += check_document("realization", yaml.safe_load(p.read_text()), ctx, rel)
    reg = root / "features" / "registry.yaml"
    if reg.is_file():
        data = yaml.safe_load(reg.read_text())
        for i, entry in enumerate(data.get("features", [])):
            out += check_document("registry_entry", entry, ctx, f"registry.features[{i}]")
    try:
        _ = ctx.concepts.concepts, ctx.concepts.realizations
    except (ValidationError, ValueError) as e:
        out.append(Finding("schema", "error", "definitions", str(e)))
    return out


def errors(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == "error"]
