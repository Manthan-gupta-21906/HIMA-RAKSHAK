# Flood Hazard Data Readiness Report

**Generated**: Pilot Phase Baseline Assessment  
**Status**: `INSUFFICIENT_LABELS` (Baseline telemetry available; verified ground truth flood impact events pending)

---

## 1. Executive Summary
In accordance with engineering standards, machine learning models for disaster early-warning must never be trained on synthetic or invented target labels. While observational telemetry (rainfall and river stages) is captured via the ingestion pipeline, verified historical ground-truth flood inundation events have not yet been certified for the pilot stations.

Therefore, training fails explicitly, and this data-readiness report establishes the data inventory, gap analysis, and requirements for model activation.

---

## 2. Sensor & Feature Coverage
- **Station Telemetry**: Rainfall (1h, 24h, 72h antecedent) and river water levels.
- **Geographic Pilot**: Kullu, Manali, Rishikesh, and Chamoli river basins.
- **Telemetry Ingestion**: Operational via CSV batch loader and geospatial spatial join service.

---

## 3. Missing Ground-Truth Labels & Gaps
1. **Absence of Disaster Event Registry**:
   - Official historical flood events with verified start, peak, and recession times are required.
2. **Class Imbalance & Negative Sampling**:
   - High-water non-flood events must be distinguished from inundation emergencies.
3. **Sensor Gaps**:
   - Upstream telemetry latency varies between 15 and 60 minutes.

---

## 4. Activation Criteria
Training the flood baseline classifier (`feat-flood-baseline`) is authorized once:
1. Minimum 10 verified historical flood events and 10 verified baseline non-events are linked to pilot stations.
2. Chronological split validation shows zero temporal leakage.
3. Precision, Recall, F1, and Brier Score meet baseline disaster response thresholds.
