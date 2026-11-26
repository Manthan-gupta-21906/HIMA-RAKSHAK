# Flood Baseline Model Documentation

## Purpose & Architecture
The flood baseline model provides a reproducible, auditable binary classification pipeline for predicting regional flood events based on engineered hydrological features.

## Model Details
- **Architecture**: Standardized logistic regression with deterministic gradient descent and L2 regularization.
- **Inputs**:
  - `rain_1h_mm`: Cumulative 1-hour rainfall
  - `rain_24h_mm`: Cumulative 24-hour rainfall
  - `antecedent_rain_72h_mm`: Antecedent rainfall over 72 hours
  - `river_level_m`: Current river stage
  - `river_level_rate_m_per_h`: Rate of river stage change per hour
  - `drainage_density`: Static or semi-static terrain drainage factor
- **Imbalance-Aware Metrics**:
  - Matthews Correlation Coefficient (MCC)
  - Brier Score (mean squared error of predicted probabilities)
  - Precision, Recall, and F1-score

## Temporal Integrity & Anti-Leakage Protocol
- Features are strictly computed up to `cutoff_at` time.
- All train/validation/test splits are performed chronologically (`max(train_timestamp) < min(test_timestamp)`).
- Leakage audits enforce that no future observations inform earlier predictions.

## Strict Label Policy
In adherence to the core requirement: **if verified labels are unavailable or insufficient, training fails explicitly and a data-readiness report is produced instead of claiming synthetic model performance.**
