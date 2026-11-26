"""Dataset preparation, temporal splitting, leakage verification, and label readiness."""

from collections.abc import Sequence
from datetime import datetime

from pydantic import BaseModel, Field

from app.features.flood import FloodFeatureVector


class FloodSample(BaseModel):
    """A single observation instance with flood feature vector and optional label."""

    sample_id: str
    location_id: str
    timestamp: datetime
    features: FloodFeatureVector
    label: int | None = None  # 1 for flood event, 0 for non-event, None if unverified


class SplitDataset(BaseModel):
    """Chronologically split dataset for training, validation, and testing."""

    train: list[FloodSample]
    val: list[FloodSample]
    test: list[FloodSample]
    feature_names: list[str]


class ReadinessReport(BaseModel):
    """Data readiness audit when historical verified labels are insufficient or absent."""

    status: str  # "INSUFFICIENT_LABELS" | "LABELLED_READY"
    total_samples: int
    labelled_samples: int
    positive_events: int
    negative_events: int
    unlabelled_samples: int
    min_timestamp: datetime | None = None
    max_timestamp: datetime | None = None
    reasons: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


FEATURE_KEYS = [
    "rain_1h_mm",
    "rain_24h_mm",
    "antecedent_rain_72h_mm",
    "river_level_m",
    "river_level_rate_m_per_h",
    "drainage_density",
]


def extract_feature_array(sample: FloodSample, fill_missing: float = 0.0) -> list[float]:
    """Extract ordered numerical feature array from a FloodSample."""
    vals = []
    vector = sample.features
    for key in FEATURE_KEYS:
        fv = getattr(vector, key, None)
        if fv is None or fv.value is None or fv.is_missing:
            vals.append(fill_missing)
        else:
            vals.append(float(fv.value))
    return vals


def check_temporal_leakage(
    train: Sequence[FloodSample],
    test: Sequence[FloodSample],
) -> tuple[bool, str | None]:
    """Verify that no training timestamp is greater than or equal to any test timestamp."""
    if not train or not test:
        return True, None

    max_train_ts = max(s.timestamp for s in train)
    min_test_ts = min(s.timestamp for s in test)

    if max_train_ts >= min_test_ts:
        msg = (
            f"Temporal leakage detected: max train timestamp {max_train_ts} >= "
            f"min test timestamp {min_test_ts}"
        )
        return False, msg

    return True, None


def chronological_split(
    samples: Sequence[FloodSample],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
) -> SplitDataset:
    """Split samples chronologically by timestamp into train, val, and test subsets."""
    if not samples:
        return SplitDataset(train=[], val=[], test=[], feature_names=FEATURE_KEYS)

    # Sort strictly by timestamp
    sorted_samples = sorted(samples, key=lambda s: s.timestamp)

    n = len(sorted_samples)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train_set = sorted_samples[:n_train]
    val_set = sorted_samples[n_train : n_train + n_val]
    test_set = sorted_samples[n_train + n_val :]

    # Assert no leakage
    ok_val, msg_val = check_temporal_leakage(train_set, val_set)
    if not ok_val:
        raise ValueError(msg_val)

    ok_test, msg_test = check_temporal_leakage(val_set or train_set, test_set)
    if not ok_test:
        raise ValueError(msg_test)

    return SplitDataset(
        train=train_set,
        val=val_set,
        test=test_set,
        feature_names=FEATURE_KEYS,
    )


def audit_label_readiness(
    samples: Sequence[FloodSample],
    min_positive: int = 5,
    min_negative: int = 5,
) -> ReadinessReport:
    """Audit label sufficiency and generate a readiness report."""
    total = len(samples)
    labelled = [s for s in samples if s.label is not None]
    pos = sum(1 for s in labelled if s.label == 1)
    neg = sum(1 for s in labelled if s.label == 0)
    unlabelled = total - len(labelled)

    min_ts = min((s.timestamp for s in samples), default=None)
    max_ts = max((s.timestamp for s in samples), default=None)

    reasons = []
    recs = []

    if not labelled:
        reasons.append("No historical flood events or non-events with verified labels found.")
        recs.append("Integrate official disaster registry or flood logs before training.")
    elif pos < min_positive:
        reasons.append(
            f"Insufficient positive flood event labels ({pos} found, min {min_positive} required)."
        )
        recs.append("Curate confirmed historical flood inundation and flash flood events.")
    elif neg < min_negative:
        reasons.append(
            f"Insufficient negative event labels ({neg} found, min {min_negative} required)."
        )
        recs.append("Sample verified non-flood baseline periods under normal conditions.")

    status = "LABELLED_READY" if not reasons else "INSUFFICIENT_LABELS"

    return ReadinessReport(
        status=status,
        total_samples=total,
        labelled_samples=len(labelled),
        positive_events=pos,
        negative_events=neg,
        unlabelled_samples=unlabelled,
        min_timestamp=min_ts,
        max_timestamp=max_ts,
        reasons=reasons,
        recommendations=recs,
    )
