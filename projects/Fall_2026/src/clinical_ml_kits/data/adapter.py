"""Dataset adapter protocol (contracts/dataset-adapter.md).

Generic framework code depends only on this protocol. Adapter packages are reached only through
``clinical_ml_kits.data.registry``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import pandas as pd

from clinical_ml_kits.data.policy import DataEnvironmentPolicy
from clinical_ml_kits.features.concept_sets import ConceptSetRealization


@dataclass(frozen=True)
class DatasetMetadata:
    id: str
    version: str
    environment: str  # synthetic | public | all_of_us_workbench
    namespace: str  # synthetic | omop
    supports: frozenset[str] = field(default_factory=frozenset)


@runtime_checkable
class DatasetAdapter(Protocol):
    def metadata(self) -> DatasetMetadata: ...

    def policy(self) -> DataEnvironmentPolicy: ...

    def resolve(self, logical_concept: str) -> ConceptSetRealization:
        """Realization in this adapter's namespace; raises PendingVerification if unusable."""
        ...

    def persons(self, person_ids: Sequence[str] | None = None) -> pd.DataFrame: ...

    def observations(
        self,
        domain: str | None = None,
        concepts: Sequence[str] | None = None,
        person_ids: Sequence[str] | None = None,
        before: pd.Timestamp | None = None,
        after: pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Observation rows; ``before`` is an EXCLUSIVE upper bound on ``start_time``."""
        ...

    def visits(
        self, person_ids: Sequence[str] | None = None, before: pd.Timestamp | None = None
    ) -> pd.DataFrame: ...

    def index_candidates(self, visit_concepts: Sequence[str] | None = None) -> pd.DataFrame:
        """Eligible index visits: ``person_id, index_time, index_visit_id, visit_type``."""
        ...
