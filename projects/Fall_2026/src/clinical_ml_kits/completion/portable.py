"""Portable project definition: kit files + metadata; no data rows, no trained artifact."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

_KIT_FILES = ("kit.yaml", "phenotype.yaml", "verification.yaml", "kit.ipynb")


def export_portable_definition(kit: Any, out_dir: str | Path) -> Path:
    out = Path(out_dir)
    src = kit._loaded.kit_dir
    kit.adapter.policy().check_write_path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name in _KIT_FILES:
        if (src / name).is_file():
            shutil.copy2(src / name, out / name)
    docs = src / kit.definition.docs
    if docs.is_dir():
        shutil.copytree(docs, out / "docs", dirs_exist_ok=True)
    meta = {
        "kit_id": kit.kit_id,
        "kit_version": kit.definition.kit_version,
        "kit_definition_hash": kit._loaded.content_hash(),
        "phenotype_version": kit.phenotype.version,
        "template_family": kit.definition.template_family,
        "feature_columns": list(kit.feature_spec.columns),
        "envelope_contract_version": "1.0.0",
        "run_manifest": (
            kit._data.run_manifest.model_dump(mode="json")
            if kit._data is not None and kit._data.run_manifest
            else None
        ),
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2, sort_keys=True, default=str))
    return out
