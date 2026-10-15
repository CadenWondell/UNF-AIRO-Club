"""Framework error classes. Methodological failures raise; they are never silently tolerated."""

from __future__ import annotations


class KitValidationError(ValueError):
    """A kit definition (or a related definition file) is invalid at the requested level."""

    def __init__(self, field: str, message: str, *, level: str | None = None) -> None:
        self.field = field
        self.level = level
        self.message = message
        where = f" [level={level}]" if level else ""
        super().__init__(f"{field}: {message}{where}")


class LeakageError(RuntimeError):
    """Base class for every ML-validity (leakage) failure."""


class PatientLeakageError(LeakageError):
    """A person appears in more than one partition (or CV fold side)."""


class TemporalLeakageError(LeakageError):
    """A feature used an observation at or after its effective cutoff."""


class SameDayLeakageError(TemporalLeakageError):
    """An index-day / index-encounter / workup observation reached a feature against policy."""


class TargetLeakageError(LeakageError):
    """A model input's logical concept is label-defining (target-defining)."""


class LabelLeakageError(LeakageError):
    """An observation used to construct the label was used as a predictor."""


class ProhibitedFeatureError(LeakageError):
    """A prohibited feature/concept/domain was requested or included without justification."""


class PreprocessingLeakageError(LeakageError):
    """A learned preprocessing step was fitted on rows other than the training partition."""


class EnvironmentNotPermitted(PermissionError):
    """A data source was requested outside the environment its data-use rules require."""


class PolicyViolation(PermissionError):
    """An action is forbidden by the active DataEnvironmentPolicy (e.g., portable export)."""


class PendingVerification(RuntimeError):
    """A behavior depends on an external fact (V-xx) that has not been verified."""

    def __init__(self, item_id: str, detail: str = "") -> None:
        self.item_id = item_id
        msg = f"Pending verification {item_id}"
        super().__init__(f"{msg}: {detail}" if detail else msg)
