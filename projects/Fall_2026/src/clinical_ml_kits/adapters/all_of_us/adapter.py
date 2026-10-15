"""All of Us adapter (namespace ``omop``): Workbench-only, fails closed.

Participant-level All of Us data is processed only inside the All of Us Researcher Workbench.
This adapter refuses to initialize anywhere else (before any data access) and never falls back to
another data source. Until V-10 (access pattern) and V-11 (populated tables) are verified, it
contains no queries: every data method raises ``PendingVerification("V-10/V-11")``.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

import pandas as pd

from clinical_ml_kits.core.environment import is_all_of_us_workbench
from clinical_ml_kits.core.errors import EnvironmentNotPermitted, PendingVerification
from clinical_ml_kits.core.paths import project_root
from clinical_ml_kits.data.adapter import DatasetMetadata
from clinical_ml_kits.data.policy import DataEnvironmentPolicy, policy_for
from clinical_ml_kits.features.concept_sets import ConceptRepository, ConceptSetRealization

REFUSAL = (
    "All of Us mode runs only inside the All of Us Researcher Workbench. This environment is not "
    "a verified Workbench (or Workbench detection is pending verification V-10), so no "
    "participant-level access was attempted. Use data_source='synthetic' outside the Workbench."
)


class AllOfUsAdapter:
    namespace = "omop"

    def __init__(self, definitions_dir: Path) -> None:
        if not is_all_of_us_workbench(definitions_dir):
            raise EnvironmentNotPermitted(REFUSAL)
        self._repo = ConceptRepository(definitions_dir)

    @classmethod
    def create(cls, root: Path | None = None, **_: object) -> AllOfUsAdapter:
        return cls((Path(root) if root else project_root()) / "definitions")

    def metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            id="all_of_us",
            version="UNVERIFIED",  # CDR version naming pending V-10
            environment="all_of_us_workbench",
            namespace=self.namespace,
        )

    def policy(self) -> DataEnvironmentPolicy:
        return policy_for("all_of_us_workbench")

    def resolve(self, logical_concept: str) -> ConceptSetRealization:
        try:
            return self._repo.realization(self.namespace, logical_concept)
        except KeyError as e:
            raise PendingVerification("V-25", str(e)) from None

    def _pending(self) -> NoReturn:
        raise PendingVerification(
            "V-10/V-11",
            "All of Us queries are not implemented until the access pattern and "
            "populated OMOP tables are verified",
        )

    def persons(self, person_ids: Sequence[str] | None = None) -> pd.DataFrame:
        self._pending()

    def observations(
        self,
        domain: str | None = None,
        concepts: Sequence[str] | None = None,
        person_ids: Sequence[str] | None = None,
        before: pd.Timestamp | None = None,
        after: pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        self._pending()

    def visits(
        self, person_ids: Sequence[str] | None = None, before: pd.Timestamp | None = None
    ) -> pd.DataFrame:
        self._pending()

    def index_candidates(self, visit_concepts: Sequence[str] | None = None) -> pd.DataFrame:
        self._pending()
