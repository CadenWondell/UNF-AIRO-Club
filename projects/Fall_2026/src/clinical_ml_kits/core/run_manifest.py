"""RunManifest (research R-19): everything needed to reproduce a run, content-hashed."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

import clinical_ml_kits

_LIBS = ("numpy", "pandas", "scikit-learn", "pydantic", "PyYAML", "matplotlib", "joblib")


def library_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    for lib in _LIBS:
        try:
            out[lib] = metadata.version(lib)
        except metadata.PackageNotFoundError:
            out[lib] = "not-installed"
    return out


def framework_git_commit() -> str | None:
    """Git commit of the framework checkout, when running from a checkout (else None)."""
    here = Path(__file__).resolve().parent
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=here, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


class RunManifest(BaseModel):
    framework_version: str = Field(default=clinical_ml_kits.__version__)
    git_commit: str | None = None
    kit_id: str
    kit_definition_hash: str
    kit_version: str
    phenotype_version: str
    concept_set_versions: dict[str, str] = Field(default_factory=dict)
    feature_registry_version: str
    dataset_id: str
    dataset_version: str
    adapter: str
    environment: str
    seed: int
    split_salt: str
    split_salt_version: int
    split_manifest_digest: str | None = None
    control_sampling_seed: int | None = None
    synthetic_population: dict[str, Any] | None = None
    library_versions: dict[str, str] = Field(default_factory=library_versions)
    framework_cell_hashes: dict[str, str] = Field(default_factory=dict)
    test_access_log: list[datetime] = Field(default_factory=list)

    def content_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def record_test_access(self) -> datetime:
        now = datetime.now(timezone.utc)
        self.test_access_log.append(now)
        return now
