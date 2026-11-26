"""Evaluation metrics, imbalance-aware evaluation, and classification report."""

import math

from pydantic import BaseModel


class FloodMetrics(BaseModel):
    """Evaluation metrics for flood baseline classification."""

    total_samples: int
    positive_samples: int
    negative_samples: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    brier_score: float  # Mean squared error of predicted probabilities
    matthews_corrcoef: float  # Imbalance-aware Matthews Correlation Coefficient (MCC)


def compute_metrics(
    y_true: list[int],
    y_pred: list[int],
    y_prob: list[float] | None = None,
) -> FloodMetrics:
    """Compute classification metrics including precision, recall, F1, and Brier/MCC."""
    if len(y_true) != len(y_pred):
        raise ValueError("Length of y_true and y_pred must match.")

    n = len(y_true)
    if n == 0:
        return FloodMetrics(
            total_samples=0,
            positive_samples=0,
            negative_samples=0,
            true_positives=0,
            false_positives=0,
            true_negatives=0,
            false_negatives=0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            accuracy=0.0,
            brier_score=0.0,
            matthews_corrcoef=0.0,
        )

    tp = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 1 and yp == 1)
    fp = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 0 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 0 and yp == 0)
    fn = sum(1 for yt, yp in zip(y_true, y_pred, strict=True) if yt == 1 and yp == 0)

    pos = tp + fn
    neg = tn + fp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / n

    # Imbalance-aware metric: Brier Score (lower is better, range [0, 1])
    if y_prob is not None and len(y_prob) == n:
        brier = sum((p - yt) ** 2 for yt, p in zip(y_true, y_prob, strict=True)) / n
    else:
        brier = sum((yp - yt) ** 2 for yt, yp in zip(y_true, y_pred, strict=True)) / n

    # Imbalance-aware metric: Matthews Correlation Coefficient (MCC)
    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn) - (fp * fn)) / denom if denom > 0 else 0.0

    return FloodMetrics(
        total_samples=n,
        positive_samples=pos,
        negative_samples=neg,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1_score=round(f1, 4),
        accuracy=round(accuracy, 4),
        brier_score=round(brier, 4),
        matthews_corrcoef=round(mcc, 4),
    )
