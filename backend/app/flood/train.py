"""Training orchestration for flood baseline with explicit label verification."""

from datetime import UTC, datetime

from pydantic import BaseModel

from app.flood.dataset import (
    FloodSample,
    SplitDataset,
    audit_label_readiness,
    chronological_split,
    extract_feature_array,
)
from app.flood.evaluate import FloodMetrics, compute_metrics
from app.flood.model import FloodBaselineClassifier, ModelMetadata


class InsufficientLabelsError(ValueError):
    """Raised when training is attempted on insufficient or unverified labels."""


class TrainingResult(BaseModel):
    """Artifact of a reproducible baseline training run."""

    metadata: ModelMetadata
    train_metrics: FloodMetrics
    val_metrics: FloodMetrics
    test_metrics: FloodMetrics


def train_flood_baseline(
    samples: list[FloodSample],
    min_positive: int = 5,
    min_negative: int = 5,
    epochs: int = 200,
    learning_rate: float = 0.05,
    l2_reg: float = 0.01,
) -> tuple[FloodBaselineClassifier, TrainingResult]:
    """Train flood baseline model, enforcing verified labels and zero leakage."""
    readiness = audit_label_readiness(
        samples, min_positive=min_positive, min_negative=min_negative
    )

    if readiness.status != "LABELLED_READY":
        reasons_str = "; ".join(readiness.reasons)
        raise InsufficientLabelsError(
            f"Cannot train flood baseline: {reasons_str}. "
            "A data-readiness report must be produced instead."
        )

    # Filter to labelled samples
    labelled_samples = [s for s in samples if s.label is not None]

    split: SplitDataset = chronological_split(labelled_samples)

    if not split.train:
        raise InsufficientLabelsError("Training split is empty after chronological splitting.")

    X_train = [extract_feature_array(s) for s in split.train]
    y_train = [s.label for s in split.train]  # type: ignore[misc]

    model = FloodBaselineClassifier(
        learning_rate=learning_rate,
        epochs=epochs,
        l2_reg=l2_reg,
    )
    model.fit(X_train, y_train, feature_names=split.feature_names)
    model.metadata.trained_at = datetime.now(UTC).isoformat()

    # Train metrics
    y_prob_train = model.predict_proba(X_train)
    y_pred_train = model.predict(X_train)
    train_metrics = compute_metrics(y_train, y_pred_train, y_prob_train)

    # Val metrics
    if split.val:
        X_val = [extract_feature_array(s) for s in split.val]
        y_val = [s.label for s in split.val]  # type: ignore[misc]
        y_prob_val = model.predict_proba(X_val)
        y_pred_val = model.predict(X_val)
        val_metrics = compute_metrics(y_val, y_pred_val, y_prob_val)
    else:
        val_metrics = compute_metrics([], [])

    # Test metrics
    if split.test:
        X_test = [extract_feature_array(s) for s in split.test]
        y_test = [s.label for s in split.test]  # type: ignore[misc]
        y_prob_test = model.predict_proba(X_test)
        y_pred_test = model.predict(X_test)
        test_metrics = compute_metrics(y_test, y_pred_test, y_prob_test)
    else:
        test_metrics = compute_metrics([], [])

    result = TrainingResult(
        metadata=model.metadata,
        train_metrics=train_metrics,
        val_metrics=val_metrics,
        test_metrics=test_metrics,
    )

    return model, result
