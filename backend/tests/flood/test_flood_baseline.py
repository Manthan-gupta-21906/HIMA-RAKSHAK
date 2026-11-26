"""Tests for flood baseline dataset preparation, model, evaluation, prediction, and label audits."""

from datetime import UTC, datetime, timedelta

import pytest

from app.features.flood import FloodFeatureVector
from app.features.metadata import FeatureValue
from app.flood.dataset import (
    FloodSample,
    audit_label_readiness,
    check_temporal_leakage,
    chronological_split,
)
from app.flood.evaluate import compute_metrics
from app.flood.predict import classify_risk_class, predict_flood_risk
from app.flood.train import InsufficientLabelsError, train_flood_baseline
from app.schemas.common import FreshnessStatus, RiskClass


def _make_dummy_feature_vector(
    location_id: str,
    cutoff_at: datetime,
    rain_1h: float = 10.0,
    rain_24h: float = 50.0,
    antecedent_72h: float = 80.0,
    river_level: float = 3.5,
    river_rate: float = 0.2,
    drainage: float = 1.2,
) -> FloodFeatureVector:
    return FloodFeatureVector(
        location_id=location_id,
        cutoff_at=cutoff_at,
        rain_1h_mm=FeatureValue(name="rain_1h_mm", value=rain_1h, unit="mm", is_missing=False),
        rain_24h_mm=FeatureValue(name="rain_24h_mm", value=rain_24h, unit="mm", is_missing=False),
        antecedent_rain_72h_mm=FeatureValue(
            name="antecedent_rain_72h_mm", value=antecedent_72h, unit="mm", is_missing=False
        ),
        river_level_m=FeatureValue(
            name="river_level_m", value=river_level, unit="m", is_missing=False
        ),
        river_level_rate_m_per_h=FeatureValue(
            name="river_level_rate_m_per_h", value=river_rate, unit="m/h", is_missing=False
        ),
        drainage_density=FeatureValue(
            name="drainage_density", value=drainage, unit="km/km2", is_missing=False
        ),
        missing_count=0,
        overall_freshness=FreshnessStatus.FRESH,
    )


def test_chronological_split_and_leakage_check():
    """Verify chronological split guarantees zero temporal leakage."""
    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    samples = []
    for i in range(20):
        ts = base_time + timedelta(hours=i * 6)
        fv = _make_dummy_feature_vector("loc-1", ts)
        samples.append(
            FloodSample(
                sample_id=f"sample-{i}",
                location_id="loc-1",
                timestamp=ts,
                features=fv,
                label=1 if i % 2 == 0 else 0,
            )
        )

    split = chronological_split(samples, train_ratio=0.6, val_ratio=0.2)
    assert len(split.train) == 12
    assert len(split.val) == 4
    assert len(split.test) == 4

    # Assert train timestamps are strictly earlier than val/test
    ok, msg = check_temporal_leakage(split.train, split.val)
    assert ok is True
    assert msg is None

    ok_test, msg_test = check_temporal_leakage(split.val, split.test)
    assert ok_test is True
    assert msg_test is None


def test_leakage_detection_raises_error():
    """Verify check_temporal_leakage correctly detects overlapping timestamps."""
    t1 = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
    t2 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)

    s1 = FloodSample(
        sample_id="s1",
        location_id="loc-1",
        timestamp=t1,
        features=_make_dummy_feature_vector("loc-1", t1),
    )
    s2 = FloodSample(
        sample_id="s2",
        location_id="loc-1",
        timestamp=t2,
        features=_make_dummy_feature_vector("loc-1", t2),
    )

    # Passing s1 (later) in train and s2 (earlier) in test must fail
    ok, msg = check_temporal_leakage([s1], [s2])
    assert ok is False
    assert "Temporal leakage detected" in msg


def test_audit_label_readiness_insufficient_labels():
    """Verify readiness audit reports insufficient labels when labels are missing."""
    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    # Samples without labels
    unlabelled = [
        FloodSample(
            sample_id=f"u-{i}",
            location_id="loc-1",
            timestamp=base_time + timedelta(hours=i),
            features=_make_dummy_feature_vector("loc-1", base_time + timedelta(hours=i)),
            label=None,
        )
        for i in range(10)
    ]

    report = audit_label_readiness(unlabelled)
    assert report.status == "INSUFFICIENT_LABELS"
    assert report.labelled_samples == 0
    assert len(report.reasons) > 0
    assert len(report.recommendations) > 0


def test_training_fails_explicitly_on_insufficient_labels():
    """Verify training aborts with InsufficientLabelsError when verified labels are absent."""
    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    samples = [
        FloodSample(
            sample_id=f"s-{i}",
            location_id="loc-1",
            timestamp=base_time + timedelta(hours=i),
            features=_make_dummy_feature_vector("loc-1", base_time + timedelta(hours=i)),
            label=None,
        )
        for i in range(10)
    ]

    with pytest.raises(InsufficientLabelsError) as exc_info:
        train_flood_baseline(samples)

    assert "Cannot train flood baseline" in str(exc_info.value)
    assert "A data-readiness report must be produced instead" in str(exc_info.value)


def test_metrics_computation_with_imbalance_metrics():
    """Verify metrics calculation includes precision, recall, F1, Brier score, and MCC."""
    y_true = [1, 1, 0, 0, 0, 0, 1, 0]
    y_pred = [1, 0, 0, 0, 0, 0, 1, 1]
    y_prob = [0.9, 0.4, 0.1, 0.2, 0.1, 0.1, 0.85, 0.6]

    metrics = compute_metrics(y_true, y_pred, y_prob)
    assert metrics.total_samples == 8
    assert metrics.true_positives == 2
    assert metrics.false_positives == 1
    assert metrics.false_negatives == 1
    assert metrics.precision > 0.0
    assert metrics.recall > 0.0
    assert metrics.f1_score > 0.0
    assert 0.0 <= metrics.brier_score <= 1.0
    assert -1.0 <= metrics.matthews_corrcoef <= 1.0


def test_training_and_inference_reproducibility():
    """Verify reproducible training, metadata emission, and risk prediction output."""
    base_time = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    samples = []
    # Create 20 labelled samples (10 positive, 10 negative)
    for i in range(20):
        ts = base_time + timedelta(hours=i * 2)
        # Higher rain and river level corresponds to label=1
        is_flood = 1 if i % 2 == 0 else 0
        rain = 40.0 if is_flood else 2.0
        river = 5.0 if is_flood else 1.0
        fv = _make_dummy_feature_vector(
            "loc-1", ts, rain_1h=rain, rain_24h=rain * 2, river_level=river
        )
        samples.append(
            FloodSample(
                sample_id=f"samp-{i}",
                location_id="loc-1",
                timestamp=ts,
                features=fv,
                label=is_flood,
            )
        )

    model1, res1 = train_flood_baseline(samples, min_positive=5, min_negative=5, epochs=100)
    model2, res2 = train_flood_baseline(samples, min_positive=5, min_negative=5, epochs=100)

    # Assert deterministic weights and bias
    assert len(model1.weights) == len(model2.weights)
    for w1, w2 in zip(model1.weights, model2.weights, strict=True):
        assert pytest.approx(w1, abs=1e-6) == w2
    assert pytest.approx(model1.bias, abs=1e-6) == model2.bias

    # Test prediction carrying version, risk level, and limitations
    test_fv = _make_dummy_feature_vector(
        "loc-1", base_time + timedelta(days=5), rain_1h=60.0, rain_24h=120.0, river_level=6.5
    )
    pred_output = predict_flood_risk(model1, test_fv)

    assert pred_output.location_id == "loc-1"
    assert pred_output.model_version == "0.1.0"
    assert len(pred_output.limitations) > 0
    assert pred_output.risk_class in [
        RiskClass.LOW,
        RiskClass.MODERATE,
        RiskClass.HIGH,
        RiskClass.SEVERE,
    ]
    assert 0.0 <= pred_output.flood_probability <= 1.0


def test_risk_level_threshold_classification():
    """Verify probability mapping to standardized RiskClass."""
    assert classify_risk_class(0.85) == RiskClass.SEVERE
    assert classify_risk_class(0.65) == RiskClass.HIGH
    assert classify_risk_class(0.40) == RiskClass.MODERATE
    assert classify_risk_class(0.10) == RiskClass.LOW
