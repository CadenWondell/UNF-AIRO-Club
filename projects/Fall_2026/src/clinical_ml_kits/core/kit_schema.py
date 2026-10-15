"""Kit definition schema (contracts/kit-definition.md) and validation levels.

Pydantic models cover structure and intra-document rules. ``validate_kit`` adds the cross-file
checks (feature registry, logical concepts and realizations, synthetic population, V-14 record,
KitDocs, FR-081 evidence) for one of the four levels ``schema < synthetic < workbench < approval``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Annotated, Any, Literal, Union

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    Tag,
    ValidationError,
    field_validator,
    model_validator,
)

from clinical_ml_kits.core.errors import KitValidationError, PendingVerification
from clinical_ml_kits.core.values import (
    ClinicalValue,
    Duration,
    Provisional,
    Sourced,
    Unverified,
    iter_provenance,
    iter_value_states,
    state_of,
)
from clinical_ml_kits.features.concept_sets import LOGICAL_ID, SEMVER
from clinical_ml_kits.provenance.models import Deviation, ProvenanceRef

__all__ = [
    "LEVELS",
    "KitDefinition",
    "LoadedKit",
    "PhenotypeDefinition",
    "Provisional",
    "RuleExpr",
    "Sourced",
    "TemporalPolicy",
    "Unverified",
    "ValidationContext",
    "load_kit_definition",
    "validate_kit",
]

LEVELS: tuple[str, ...] = ("schema", "synthetic", "workbench", "approval")
Level = Literal["schema", "synthetic", "workbench", "approval"]
Status = Literal["draft", "requires_verification", "verified", "approved"]
TEMPLATE_FAMILIES: dict[str, set[str]] = {"binary_tabular": {"current_state"}}
LogicalId = Annotated[str, Field(pattern=LOGICAL_ID)]
SemVer = Annotated[str, Field(pattern=SEMVER)]
Op = Literal["<", "<=", ">", ">="]
_STRICT = ConfigDict(extra="forbid")

# --------------------------------------------------------------------------- RuleExpr


class _Counted(BaseModel):
    model_config = _STRICT
    min_count: int | ClinicalValue[int] = 1

    @field_validator("min_count")
    @classmethod
    def _plain_count_is_one(cls, v: object) -> object:
        if isinstance(v, int) and v != 1:
            raise ValueError("min_count other than 1 is a clinical value: use a value state")
        return v


class HasEvent(_Counted):
    concept: LogicalId
    within: ClinicalValue[Duration] | None = None
    distinct_days: bool = False


class MeasurementPredicate(_Counted):
    concept: LogicalId
    op: Op
    value: ClinicalValue[float]
    unit: str | None = None
    within: ClinicalValue[Duration] | None = None
    distinct_days: bool = False


class AgeAtIndex(BaseModel):
    model_config = _STRICT
    op: Op
    years: ClinicalValue[float]


class ObservationHistory(BaseModel):
    model_config = _STRICT
    min: ClinicalValue[Duration]


class VisitPredicate(_Counted):
    type_concept: LogicalId | None = None
    within: ClinicalValue[Duration] | None = None


class HasEventRule(BaseModel):
    model_config = _STRICT
    has_event: HasEvent


class MeasurementRule(BaseModel):
    model_config = _STRICT
    measurement: MeasurementPredicate


class AgeRule(BaseModel):
    model_config = _STRICT
    age_at_index: AgeAtIndex


class HistoryRule(BaseModel):
    model_config = _STRICT
    observation_history: ObservationHistory


class VisitRule(BaseModel):
    model_config = _STRICT
    visit: VisitPredicate


class AllOf(BaseModel):
    model_config = _STRICT
    all_of: list[RuleExpr] = Field(min_length=1)


class AnyOf(BaseModel):
    model_config = _STRICT
    any_of: list[RuleExpr] = Field(min_length=1)


class Not(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    not_: RuleExpr = Field(alias="not")


RuleExpr = Union[AllOf, AnyOf, Not, HasEventRule, MeasurementRule, AgeRule, HistoryRule, VisitRule]
for _m in (AllOf, AnyOf, Not):
    _m.model_rebuild()


def rule_concepts(rule: object) -> set[str]:
    """Every logical concept id referenced by a rule tree."""
    out: set[str] = set()
    if isinstance(rule, (AllOf, AnyOf)):
        for r in rule.all_of if isinstance(rule, AllOf) else rule.any_of:
            out |= rule_concepts(r)
    elif isinstance(rule, Not):
        out |= rule_concepts(rule.not_)
    elif isinstance(rule, HasEventRule):
        out.add(rule.has_event.concept)
    elif isinstance(rule, MeasurementRule):
        out.add(rule.measurement.concept)
    elif isinstance(rule, VisitRule) and rule.visit.type_concept:
        out.add(rule.visit.type_concept)
    return out


# --------------------------------------------------------------------------- phenotype


class CaseIndexRule(BaseModel):
    model_config = _STRICT
    type: Literal["first_satisfied"]


class ControlIndexRule(BaseModel):
    model_config = _STRICT
    type: Literal["eligible_visit"]
    visit_types: list[LogicalId] = Field(default_factory=list)


class ControlSampling(BaseModel):
    model_config = _STRICT
    strategy: Literal["all_eligible", "random_ratio", "matched"]
    controls_per_case: ClinicalValue[float] | None = None
    match_on: list[Literal["visit_type", "calendar_year", "sex_at_birth", "age_band"]] = Field(
        default_factory=list
    )
    seed: int
    rationale: str = Field(min_length=1)
    provenance: list[ProvenanceRef] = Field(min_length=1)

    @model_validator(mode="after")
    def _strategy_rules(self) -> ControlSampling:
        if self.strategy in ("random_ratio", "matched") and self.controls_per_case is None:
            raise ValueError(
                f"control_sampling.controls_per_case is required for strategy {self.strategy}"
            )
        if self.strategy == "all_eligible" and self.controls_per_case is not None:
            raise ValueError("control_sampling.controls_per_case must be null for all_eligible")
        if self.strategy == "matched" and not self.match_on:
            raise ValueError("control_sampling.match_on is required for strategy matched")
        return self


class PhenotypeDefinition(BaseModel):
    model_config = _STRICT
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    version: SemVer
    status: Status
    provenance: list[ProvenanceRef] = Field(min_length=1)
    deviations: list[Deviation] = Field(default_factory=list)
    case_rule: RuleExpr
    case_index_rule: CaseIndexRule
    control_rule: RuleExpr
    control_index_rule: ControlIndexRule
    control_sampling: ControlSampling
    min_observation_history: ClinicalValue[Duration]
    repeat_evidence: RuleExpr | None = None
    label_defining_concepts: list[LogicalId] = Field(min_length=1)
    description: str = ""

    def concepts(self) -> set[str]:
        out = rule_concepts(self.case_rule) | rule_concepts(self.control_rule)
        if self.repeat_evidence is not None:
            out |= rule_concepts(self.repeat_evidence)
        return out | set(self.label_defining_concepts) | set(self.control_index_rule.visit_types)


class PhenotypeRef(BaseModel):
    model_config = _STRICT
    path: str
    version: SemVer


# --------------------------------------------------------------------------- kit


class DatasetRef(BaseModel):
    model_config = _STRICT
    id: str
    version: ClinicalValue[str]


class Target(BaseModel):
    model_config = _STRICT
    code: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1)


class CohortDefinition(BaseModel):
    model_config = _STRICT
    version: SemVer
    inclusion: list[RuleExpr] = Field(default_factory=list)
    exclusion: list[RuleExpr] = Field(default_factory=list)
    provenance: list[ProvenanceRef] = Field(min_length=1)

    def concepts(self) -> set[str]:
        out: set[str] = set()
        for r in [*self.inclusion, *self.exclusion]:
            out |= rule_concepts(r)
        return out


class WindowTarget(BaseModel):
    model_config = _STRICT
    concept: LogicalId | None = None
    domain: str | None = None

    @model_validator(mode="after")
    def _one(self) -> WindowTarget:
        if (self.concept is None) == (self.domain is None):
            raise ValueError("exactly one of concept or domain is required")
        return self


class WindowedExclusion(BaseModel):
    model_config = _STRICT
    target: WindowTarget
    before: ClinicalValue[Duration]
    after: ClinicalValue[Duration]
    reason: str = Field(min_length=1)


class TemporalPolicy(BaseModel):
    """No defaults for ``same_day`` and ``exclude_index_encounter`` (R-12, FR-137)."""

    model_config = _STRICT
    same_day: ClinicalValue[Literal["include", "exclude_index_day"]]
    exclude_index_encounter: ClinicalValue[bool]
    washout: ClinicalValue[Duration]
    lookback: ClinicalValue[Duration]
    windowed_exclusions: list[WindowedExclusion] = Field(default_factory=list)


DERIVATION = re.compile(
    r"^(latest|previous|delta|pct_change|mean|min|max|std|slope|count|time_since_last"
    r"|rolling_mean\(P\d+[DW]\))$"
)
EVENT_DERIVATIONS = {"count", "time_since_last"}


class FeatureSelection(BaseModel):
    model_config = _STRICT
    feature: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    derivations: list[str] = Field(min_length=1)
    window: Duration | None = None

    @field_validator("derivations")
    @classmethod
    def _known(cls, v: list[str]) -> list[str]:
        bad = [d for d in v if not DERIVATION.match(d)]
        if bad:
            raise ValueError(f"unknown derivations {bad}")
        if len(set(v)) != len(v):
            raise ValueError("duplicate derivations")
        return v


class ProhibitedItem(BaseModel):
    model_config = _STRICT
    feature: str | None = None
    concept: LogicalId | None = None
    domain: str | None = None
    reason: str = Field(min_length=1)
    provenance: list[ProvenanceRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def _one(self) -> ProhibitedItem:
        if sum(x is not None for x in (self.feature, self.concept, self.domain)) != 1:
            raise ValueError("exactly one of feature, concept, or domain is required")
        return self


class JustifiedInclusion(BaseModel):
    model_config = _STRICT
    item: str
    rationale: str = Field(min_length=1)
    provenance: list[ProvenanceRef] = Field(default_factory=list)


class LeakageRisk(BaseModel):
    model_config = _STRICT
    description: str = Field(min_length=1)
    mitigation: str = Field(min_length=1)


class Missingness(BaseModel):
    model_config = _STRICT
    strategy: Literal["median_impute_with_indicator"]
    min_features_present: int | None = Field(default=None, ge=0)


class BaselineParams(BaseModel):
    """Allow-listed LogisticRegression parameters rendered literally into the notebook."""

    model_config = _STRICT
    C: float = Field(gt=0)
    penalty: Literal["l2", "l1", "elasticnet"] | None
    class_weight: Literal["balanced"] | None
    max_iter: int = Field(gt=0)
    solver: Literal["lbfgs", "liblinear", "saga"] = "lbfgs"


class Baseline(BaseModel):
    model_config = _STRICT
    model: Literal["logistic_regression"]
    params: BaselineParams


Metric = Literal[
    "auroc",
    "auprc",
    "sensitivity",
    "specificity",
    "precision",
    "recall",
    "f1",
    "confusion_matrix",
    "brier",
]


class Calibration(BaseModel):
    model_config = _STRICT
    required: bool
    bins: int = Field(ge=2)
    strategy: Literal["quantile", "uniform"]
    method: Literal[
        "none",
        "grouped_oof_sigmoid",
        "grouped_oof_isotonic",
        "grouped_native_sigmoid",
        "grouped_native_isotonic",
    ]


class Explainability(BaseModel):
    model_config = _STRICT
    coefficients: bool
    permutation_importance: bool


class SaltChange(BaseModel):
    model_config = _STRICT
    salt_version: int = Field(ge=2)
    previous_salt: str
    reason: str = Field(min_length=10)
    changed_on: date
    previous_kit_version: SemVer
    kit_version: SemVer


def _semver(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


class SplitConfig(BaseModel):
    model_config = _STRICT
    strategy: Literal["hash", "official"]
    fractions: tuple[float, float, float]
    salt: str = Field(min_length=3)
    salt_version: int = Field(ge=1)
    salt_history: list[SaltChange] = Field(default_factory=list)
    min_positives_per_partition: int = Field(ge=1)
    prevalence_tolerance: float = Field(gt=0, lt=1)

    @model_validator(mode="after")
    def _rules(self) -> SplitConfig:
        if abs(sum(self.fractions) - 1.0) > 1e-9 or min(self.fractions) <= 0:
            raise ValueError("fractions must be positive and sum to 1")
        if not self.salt.endswith(f"-s{self.salt_version}"):
            raise ValueError(f"salt must end with '-s{self.salt_version}' (salt_version)")
        return self


class Review(BaseModel):
    model_config = _STRICT
    reviewer: str = Field(min_length=1)
    signed_on: date


def _phenotype_form(v: Any) -> str:
    if isinstance(v, dict):
        return "Ref" if "path" in v else "Inline"
    return "Ref" if isinstance(v, PhenotypeRef) else "Inline"


class KitDefinition(BaseModel):
    model_config = _STRICT
    kit_schema: Literal["1.0"]
    kit_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1)
    kit_version: SemVer
    status: Status
    dataset: DatasetRef
    template_family: str
    clinical_question: str = Field(min_length=1)
    target: Target
    prediction_type: Literal["current_state", "future_risk"]
    horizon: str | None = None
    phenotype: Annotated[
        Annotated[PhenotypeRef, Tag("Ref")] | Annotated[PhenotypeDefinition, Tag("Inline")],
        Discriminator(_phenotype_form),
    ]
    cohort: CohortDefinition
    temporal_policy: TemporalPolicy
    features: list[FeatureSelection] = Field(min_length=1)
    prohibited: list[ProhibitedItem]
    justified_inclusions: list[JustifiedInclusion] = Field(default_factory=list)
    leakage_risks: list[LeakageRisk]
    missingness: Missingness
    baseline: Baseline
    threshold_rule: str
    metrics: list[Metric] = Field(min_length=1)
    calibration: Calibration
    explainability: Explainability
    split: SplitConfig
    seed: int
    synthetic_population: str | None = None
    sources: list[ProvenanceRef] = Field(min_length=1)
    known_limitations: list[str] = Field(min_length=1)
    docs: str
    review: Review | None = None

    @field_validator("threshold_rule")
    @classmethod
    def _threshold(cls, v: str) -> str:
        if v in ("youden", "max_f1"):
            return v
        m = re.match(r"^fixed\((0(\.\d+)?|1(\.0+)?)\)$", v)
        if not m:
            raise ValueError("threshold_rule must be youden, max_f1, or fixed(<value in [0,1]>)")
        return v

    @model_validator(mode="after")
    def _cross_field(self) -> KitDefinition:
        if self.prediction_type == "current_state" and self.horizon is not None:
            raise ValueError("horizon: must be absent for prediction_type current_state")
        if self.prediction_type == "future_risk" and not self.horizon:
            raise ValueError("horizon: required for prediction_type future_risk")
        if self.template_family not in TEMPLATE_FAMILIES:
            raise ValueError(f"template_family: unknown template family {self.template_family!r}")
        if self.prediction_type not in TEMPLATE_FAMILIES[self.template_family]:
            raise ValueError(
                f"template_family: {self.template_family} does not support {self.prediction_type}"
            )
        m = set(self.metrics)
        if not ({"auprc", "f1"} & m or {"precision", "recall"} <= m):
            raise ValueError(
                "metrics: must include an imbalance-aware metric (auprc, f1, or precision+recall)"
            )
        hist = self.split.salt_history
        if len(hist) != self.split.salt_version - 1:
            raise ValueError(
                "split.salt_history: salt_version requires one salt_history entry per change"
            )
        for i, ch in enumerate(hist, start=2):
            if ch.salt_version != i:
                raise ValueError("split.salt_history: entries must be salt_version 2, 3, ...")
            if _semver(ch.kit_version) <= _semver(ch.previous_kit_version):
                raise ValueError("split.salt_history: a salt change requires a kit_version bump")
            if _semver(ch.kit_version) > _semver(self.kit_version):
                raise ValueError("split.salt_history: kit_version later than the kit's version")
        return self

    def phenotype_definition(self) -> PhenotypeDefinition:
        if isinstance(self.phenotype, PhenotypeDefinition):
            return self.phenotype
        raise RuntimeError("phenotype not resolved; use load_kit_definition")


# --------------------------------------------------------------------------- loading


@dataclass
class LoadedKit:
    definition: KitDefinition
    phenotype: PhenotypeDefinition
    path: Path
    raw: dict[str, Any]
    phenotype_raw: dict[str, Any]

    @property
    def kit_dir(self) -> Path:
        return self.path.parent

    @property
    def kit_id(self) -> str:
        return self.definition.kit_id

    def content_hash(self) -> str:
        payload = json.dumps(
            {"kit": self.raw, "phenotype": self.phenotype_raw}, sort_keys=True, default=str
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def concepts(self) -> set[str]:
        d = self.definition
        out = self.phenotype.concepts() | d.cohort.concepts()
        out |= {p.concept for p in d.prohibited if p.concept}
        out |= {w.target.concept for w in d.temporal_policy.windowed_exclusions if w.target.concept}
        return out


def _loc(err: dict[str, Any]) -> str:
    parts: list[str] = []
    for p in err["loc"]:
        if isinstance(p, int):
            parts.append(f"[{p}]")
        elif isinstance(p, str) and (
            p[:1].isupper() or "[" in p or p.startswith("function-") or p in ("not",)
        ):
            if p == "not":
                parts.append(".not")
            continue
        else:
            parts.append(f".{p}" if parts else p)
    return "".join(parts).replace(".[", "[") or "<root>"


def _wrap(exc: ValidationError, prefix: str = "") -> KitValidationError:
    issues: dict[str, str] = {}
    for e in exc.errors():
        loc = _loc(dict(e))
        msg = str(e["msg"]).removeprefix("Value error, ")
        # report the deepest message per location (union branches produce several)
        issues.setdefault(f"{prefix}{loc}", msg)
    if not issues:
        return KitValidationError(prefix or "<root>", str(exc))
    lines = [f"{k}: {v}" for k, v in issues.items()]
    first = next(iter(issues))
    err = KitValidationError(first, "; ".join(lines) if len(lines) > 1 else issues[first])
    err.issues = lines  # type: ignore[attr-defined]
    return err


def load_kit_definition(path: str | Path) -> LoadedKit:
    """Load ``kit.yaml`` (or a kit directory) and its phenotype. Raises KitValidationError."""
    p = Path(path)
    if p.is_dir():
        p = p / "kit.yaml"
    try:
        raw = yaml.safe_load(p.read_text())
    except (OSError, yaml.YAMLError) as e:
        raise KitValidationError(str(p), f"cannot read kit definition: {e}") from e
    if not isinstance(raw, dict):
        raise KitValidationError(str(p), "kit definition must be a mapping")
    try:
        kit = KitDefinition.model_validate(raw)
    except ValidationError as e:
        raise _wrap(e) from None
    if isinstance(kit.phenotype, PhenotypeDefinition):
        return LoadedKit(kit, kit.phenotype, p, raw, raw["phenotype"])
    ph_path = p.parent / kit.phenotype.path
    try:
        ph_raw = yaml.safe_load(ph_path.read_text())
        phenotype = PhenotypeDefinition.model_validate(ph_raw)
    except OSError as e:
        raise KitValidationError("phenotype.path", f"cannot read {ph_path}: {e}") from e
    except ValidationError as e:
        raise _wrap(e, "phenotype.") from None
    if phenotype.version != kit.phenotype.version:
        raise KitValidationError(
            "phenotype.version",
            f"kit pins {kit.phenotype.version} but {ph_path.name} is {phenotype.version}",
        )
    return LoadedKit(kit, phenotype, p, raw, ph_raw)


# --------------------------------------------------------------------------- context


@dataclass
class ValidationContext:
    """Where definitions, synthetic params, and sources live (project root or a fixture root)."""

    root: Path
    _cache: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_root(cls, root: str | Path | None = None) -> ValidationContext:
        from clinical_ml_kits.core.paths import project_root

        return cls(Path(root) if root else project_root())

    @property
    def definitions_dir(self) -> Path:
        return self.root / "definitions"

    @property
    def registry(self) -> Any:
        if "registry" not in self._cache:
            from clinical_ml_kits.features.registry import FeatureRegistry

            self._cache["registry"] = FeatureRegistry.load(
                self.definitions_dir / "features" / "registry.yaml"
            )
        return self._cache["registry"]

    @property
    def concepts(self) -> Any:
        if "concepts" not in self._cache:
            from clinical_ml_kits.features.concept_sets import ConceptRepository

            self._cache["concepts"] = ConceptRepository(self.definitions_dir)
        return self._cache["concepts"]

    def source(self, source_id: str) -> Any:
        from clinical_ml_kits.provenance.models import SourceRecord

        p = self.definitions_dir / "sources" / f"{source_id}.yaml"
        if not p.exists():
            return None
        return SourceRecord.model_validate(yaml.safe_load(p.read_text()))


# --------------------------------------------------------------------------- validation


def _sklearn_version() -> str:
    import sklearn

    return str(sklearn.__version__)


def native_grouped_calibration_verified(ctx: ValidationContext) -> bool:
    """True only if the V-14 record is verified and lists the running scikit-learn version."""
    rec = ctx.source("v14_grouped_calibration")
    if rec is None or rec.verification_status != "verified" or not rec.parameters:
        return False
    versions = rec.parameters.get("native_grouped_safe_sklearn_versions") or []
    return _sklearn_version() in versions


@dataclass
class ValidationReport:
    kit_id: str
    level: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    provisional: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _states(kit: LoadedKit) -> list[tuple[str, object]]:
    out = list(iter_value_states(kit.definition))
    out = [(p, v) for p, v in out if not p.startswith("phenotype.")]
    out += [(f"phenotype.{p}", v) for p, v in iter_value_states(kit.phenotype)]
    return out


def feature_concepts(kit: LoadedKit, ctx: ValidationContext) -> dict[str, str]:
    reg = ctx.registry
    return {
        f.feature: reg.get(f.feature).concept.id
        for f in kit.definition.features
        if f.feature in reg
    }


def _schema_checks(kit: LoadedKit, ctx: ValidationContext, r: ValidationReport) -> None:
    d, ph = kit.definition, kit.phenotype
    reg = ctx.registry
    for i, f in enumerate(d.features):
        if f.feature not in reg:
            r.errors.append(f"features[{i}].feature: {f.feature!r} is not in the feature registry")
            continue
        entry = reg.get(f.feature)
        if entry.value_type == "event":
            bad = set(f.derivations) - EVENT_DERIVATIONS
            if bad:
                r.errors.append(
                    f"features[{i}].derivations: {sorted(bad)} not valid for event feature"
                )
        if entry.domain == "person" and f.derivations != ["latest"]:
            r.errors.append(f"features[{i}].derivations: person features support only [latest]")
    for i, p in enumerate(d.prohibited):
        if p.feature and p.feature not in reg:
            r.errors.append(
                f"prohibited[{i}].feature: {p.feature!r} is not in the feature registry"
            )
    known = set(ctx.concepts.concepts)
    for c in sorted(kit.concepts() | set(feature_concepts(kit, ctx).values())):
        if c not in known:
            r.errors.append(
                f"concepts: logical concept {c!r} is not defined in definitions/concepts"
            )

    # Cross-field rule 1: features ∩ (prohibited ∪ label-defining) = ∅ unless justified.
    justified = {j.item for j in d.justified_inclusions}
    fc = feature_concepts(kit, ctx)
    pro_feat = {p.feature for p in d.prohibited if p.feature}
    pro_conc = {p.concept for p in d.prohibited if p.concept} | set(ph.label_defining_concepts)
    pro_dom = {p.domain for p in d.prohibited if p.domain}
    for f in d.features:
        if f.feature in justified:
            continue
        concept = fc.get(f.feature)
        dom = reg.get(f.feature).domain if f.feature in reg else None
        if f.feature in pro_feat:
            r.errors.append(f"prohibited: feature {f.feature!r} is both a feature and prohibited")
        elif concept in pro_conc:
            r.errors.append(
                f"prohibited: feature {f.feature!r} uses label-defining/prohibited "
                f"concept {concept!r}"
            )
        elif dom in pro_dom:
            r.errors.append(f"prohibited: feature {f.feature!r} is in prohibited domain {dom!r}")

    # P-4 status gating.
    if d.status in ("verified", "approved") or ph.status in ("verified", "approved"):
        for path, v in _states(kit):
            if isinstance(v, (Provisional, Unverified)):
                r.errors.append(
                    f"status: {d.status} is not allowed while {path} is {state_of(v)} (P-4)"
                )
        refs = [*iter_provenance(d), *iter_provenance(ph, "phenotype")]
        for path, ref in dict(refs).items():
            if not ref.is_verified:
                r.errors.append(
                    f"status: {d.status} is not allowed while provenance at {path} is "
                    f"{ref.verification_status} (P-4)"
                )

    if d.calibration.method.startswith(
        "grouped_native"
    ) and not native_grouped_calibration_verified(ctx):
        err = PendingVerification(
            "V-14",
            f"native grouped calibration is not verified for scikit-learn {_sklearn_version()}",
        )
        r.errors.append(f"calibration.method: {err} (PendingVerification V-14)")

    if ph.control_sampling.strategy != "all_eligible" and not any(
        "prevalence" in lim.lower() for lim in d.known_limitations
    ):
        r.errors.append(
            "known_limitations: must state that probabilities reflect the sampled development "
            "prevalence, not population prevalence"
        )


def _concept_resolution(
    kit: LoadedKit, ctx: ValidationContext, namespace: str, r: ValidationReport, level: str
) -> None:
    for c in sorted(kit.concepts() | set(feature_concepts(kit, ctx).values())):
        try:
            real = ctx.concepts.realization(namespace, c)
        except PendingVerification as e:
            r.errors.append(
                f"concepts.{c}: no usable {namespace} realization ({e}) [level={level}]"
            )
            continue
        if namespace == "omop" and not real.members and real.domain != "person":
            r.errors.append(f"concepts.{c}: omop realization has no members [level={level}]")


def validate_kit(
    kit: LoadedKit, level: str, ctx: ValidationContext | None = None
) -> ValidationReport:
    """Validate a loaded kit at ``level``; raises KitValidationError listing every issue."""
    if level not in LEVELS:
        raise ValueError(f"unknown validation level {level!r}; expected one of {LEVELS}")
    ctx = ctx or ValidationContext.from_root()
    r = ValidationReport(kit.kit_id, level)
    _schema_checks(kit, ctx, r)
    states = _states(kit)
    r.provisional = [p for p, v in states if isinstance(v, Provisional)]
    r.unverified = [p for p, v in states if isinstance(v, Unverified)]
    rank = LEVELS.index(level)
    if rank >= 1:  # synthetic
        for p in r.unverified:
            if p != "dataset.version":
                r.errors.append(f"{p}: UNVERIFIED value needed for execution [level={level}]")
        _concept_resolution(kit, ctx, "synthetic", r, level)
        d = kit.definition
        if not d.synthetic_population:
            r.errors.append(f"synthetic_population: required at this level [level={level}]")
        else:
            from clinical_ml_kits.data.registry import validate_population_params

            pp = ctx.root / d.synthetic_population
            try:
                validate_population_params(pp)
            except (OSError, ValueError) as e:
                r.errors.append(f"synthetic_population: {pp} invalid: {e} [level={level}]")
    if rank >= 2:  # workbench
        for p in r.provisional:
            r.errors.append(f"{p}: provisional (synthetic-only) value [level={level}]")
        if "dataset.version" in r.unverified:
            r.errors.append(f"dataset.version: UNVERIFIED [level={level}]")
        reg = ctx.registry
        for f in kit.definition.features:
            if f.feature not in reg:
                continue
            for p, v in iter_value_states(reg.get(f.feature), f"registry.{f.feature}"):
                if isinstance(v, (Provisional, Unverified)):
                    r.errors.append(f"{p}: {state_of(v)} [level={level}]")
        _concept_resolution(kit, ctx, "omop", r, level)
    if rank >= 3:  # approval
        _approval_checks(kit, ctx, r, level)
    if r.errors:
        err = KitValidationError(
            r.errors[0].split(":", 1)[0], "\n  ".join(["", *r.errors]), level=level
        )
        err.report = r  # type: ignore[attr-defined]
        raise err
    return r


KITDOCS = (
    "README.md",
    "clinical_background.md",
    "construction.md",
    "features.md",
    "limitations.md",
    "verification_log.md",
)


def _approval_checks(
    kit: LoadedKit, ctx: ValidationContext, r: ValidationReport, level: str
) -> None:
    d = kit.definition
    if d.review is None:
        r.errors.append(f"review: reviewer sign-off is required [level={level}]")
    docs = kit.kit_dir / d.docs
    for name in KITDOCS:
        if not (docs / name).is_file():
            r.errors.append(f"docs: missing {name} [level={level}]")
    ev = kit.kit_dir / "evidence" / "fr081.yaml"
    if not ev.is_file():
        r.errors.append(
            f"evidence: FR-081 evidence record evidence/fr081.yaml missing [level={level}]"
        )
    else:
        from clinical_ml_kits.core.evidence import FR081Evidence

        try:
            FR081Evidence.model_validate(yaml.safe_load(ev.read_text()))
        except ValidationError as e:
            r.errors.append(f"evidence: invalid fr081.yaml: {e} [level={level}]")
    if (docs / "README.md").is_file():
        from clinical_ml_kits.provenance.kitdocs import readme_issues

        for issue in readme_issues(docs):
            r.errors.append(f"docs.README.md: {issue} [level={level}]")
