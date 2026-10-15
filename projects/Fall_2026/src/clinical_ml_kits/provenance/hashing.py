"""Canonical content hashing for verified items (P-7)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from datetime import date, datetime
from typing import Any

# Verification metadata and lifecycle status are not "content": changing them must not change
# the hash, while any substantive edit must.
IGNORED_KEYS = frozenset(
    {"content_hash", "verification_status", "verified_by", "verified_on", "status", "review"}
)
REF_LIST_KEYS = ("provenance", "sources")


def canonical(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): canonical(v) for k, v in sorted(obj.items()) if k not in IGNORED_KEYS}
    if isinstance(obj, (list, tuple)):
        return [canonical(v) for v in obj]
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def content_hash(obj: Any) -> str:
    """SHA-256 of the canonical JSON form of ``obj``."""
    payload = json.dumps(canonical(obj), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _is_ref(x: Any) -> bool:
    return isinstance(x, dict) and "source_id" in x and "verification_status" in x


def iter_owned_refs(
    doc: Any, path: str = ""
) -> Iterator[tuple[dict[str, Any], dict[str, Any], str]]:
    """Yield ``(owner, ref, path)``: each inline ref and the mapping (item) it supports."""
    if isinstance(doc, dict):
        for key in REF_LIST_KEYS:
            refs = doc.get(key)
            if isinstance(refs, list):
                for i, ref in enumerate(refs):
                    if _is_ref(ref):
                        yield doc, ref, f"{path}.{key}[{i}]" if path else f"{key}[{i}]"
        for k, v in doc.items():
            if k in REF_LIST_KEYS:
                continue
            yield from iter_owned_refs(v, f"{path}.{k}" if path else str(k))
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            yield from iter_owned_refs(v, f"{path}[{i}]")


def stamp_hashes(doc: Any) -> Any:
    """Set ``content_hash`` on every verified ref to the hash of the item it supports.

    Run by a maintainer immediately after a human verification; never automatically in CI.
    """
    for owner, ref, _ in list(iter_owned_refs(doc)):
        if ref.get("verification_status") == "verified":
            ref["content_hash"] = content_hash(owner)
    return doc


def stamp_file(path: Any, header: str | None = None) -> None:
    """Stamp verified refs in a YAML file in place (comments are replaced by ``header``)."""
    from pathlib import Path

    import yaml

    p = Path(path)
    text = p.read_text()
    lead = header or "\n".join(line for line in text.splitlines() if line.startswith("#"))
    # Break YAML aliases: each ref must be its own object to carry its own item's hash.
    data = json.loads(json.dumps(yaml.safe_load(text), default=str))
    data = stamp_hashes(data)

    class _NoAlias(yaml.SafeDumper):
        def ignore_aliases(self, data: Any) -> bool:
            return True

    body = yaml.dump(data, Dumper=_NoAlias, sort_keys=False, width=100, allow_unicode=True)
    p.write_text((lead + "\n" if lead else "") + body)
