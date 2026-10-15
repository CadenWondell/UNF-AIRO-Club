"""Generate the published JSON Schemas (``docs/schemas/*.schema.json``) from the Pydantic models."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def _kit() -> dict[str, Any]:
    from clinical_ml_kits.core.kit_schema import KitDefinition

    return KitDefinition.model_json_schema()


def _envelope() -> dict[str, Any]:
    from clinical_ml_kits.prediction.envelope import PredictionEnvelope

    return PredictionEnvelope.model_json_schema()


def _provenance() -> dict[str, Any]:
    from pydantic.json_schema import models_json_schema

    from clinical_ml_kits.provenance.models import Deviation, ProvenanceRef, SourceRecord

    models: list[type[BaseModel]] = [SourceRecord, ProvenanceRef, Deviation]
    _, schema = models_json_schema(
        [(m, "validation") for m in models],
        title="Provenance (SourceRecord, ProvenanceRef, Deviation)",
    )
    return schema


SCHEMAS: dict[str, Callable[[], dict[str, Any]]] = {
    "kit-definition": _kit,
    "prediction-envelope": _envelope,
    "provenance": _provenance,
}


def render_schema(name: str) -> str:
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", **SCHEMAS[name]()}
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_schemas(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name in SCHEMAS:
        p = out_dir / f"{name}.schema.json"
        p.write_text(render_schema(name))
        written.append(p)
    return written
