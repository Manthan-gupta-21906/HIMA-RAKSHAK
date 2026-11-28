# Proposed Historical Replay API Contract

This document proposes a contract for serving curated historical replay sequences
in HIMA-RAKSHAK. It does **not** implement anything on the backend — no endpoint
exists today — and the frontend `ReplayPage` therefore continues to use clearly
labeled sample reconstructions and never pretends replay is live.

## Motivation

`GET /risk/history/{location_id}` returns per-location assessment history for
auditability, not multi-frame incident reconstructions. `ReplayPage.tsx` drives
timeline playback from `MOCK_REPLAY_EVENTS` (2014 Jhelum Basin Flood Surge and
similar sample reconstructions). To let operators replay real incidents rather
than samples, the backend needs an endpoint that returns chronological frame
sequences grouped by event, optionally filtered by location, hazard, and time.

## Proposed Endpoint

```
GET /risk/replay
```

### Query Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `location_id` | string | optional | Filter sequences to a single pilot location. |
| `hazard_type` | `"flood" \| "avalanche"` | optional | Filter frames by hazard type. |
| `since` | ISO 8601 datetime | optional | Include sequences containing frames at or after this time. |
| `limit` | integer, `1..200` | optional (default `50`) | Max frames returned per location/hazard sequence. |

### Response (200 OK)

```json
{
  "total": 2,
  "items": [
    {
      "id": "EVT-JHELUM-2014",
      "location_id": "JK-SGR-01",
      "title": "Jhelum Basin Flood Surge (2014)",
      "sector": "Anantnag - Sangam & Srinagar",
      "hazard": "flood",
      "date_range": "2014-09-04 to 2014-09-07",
      "provenance": "IMD/CWC archival record",
      "is_demo_fixture": false,
      "frames": [
        {
          "id": "f1",
          "timestamp": "2014-09-04T06:00:00+05:30",
          "phase_label": "T+00h • Onset",
          "primary_metric_label": "Sangam Gauge",
          "primary_metric_value": "14.2 ft",
          "secondary_metric_label": "6h Rainfall",
          "secondary_metric_value": "38 mm",
          "alert_tier": "Watch",
          "risk_class": "moderate",
          "score": 0.45,
          "confidence": 0.82,
          "summary": "Persistent monsoon trough over South Kashmir."
        }
      ]
    }
  ]
}
```

## Role Policy

Same as other risk-read endpoints: `viewer`, `district_operator`, or `admin`.
Read-only — no mutation, no alert creation, no official-warning creation.

## Why Not Faked Live Data

The frontend must never present sample reconstructions as live telemetry. Until
this endpoint (or an equivalent) is implemented, `ReplayPage` keeps its explicit
"Sample Reconstruction" labeling and the proposed contract lives here for a
future backend change.
