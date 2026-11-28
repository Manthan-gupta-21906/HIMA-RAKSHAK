# Historical Replay API Contract (Implemented)

This document describes the `GET /risk/replay` endpoint for serving curated
historical replay sequences in HIMA-RAKSHAK. The endpoint is implemented on the
backend and consumed by the frontend `ReplayPage`, which displays explicit
"Live Backend History" / "Sample Reconstruction" badges so sample data is never
mistaken for live telemetry.

## Endpoint

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
      "id": "replay-JK-SGR-01-flood",
      "location_id": "JK-SGR-01",
      "title": "Flood Risk History — JK-SGR-01",
      "sector": "Srinagar District, J&K",
      "hazard": "flood",
      "date_range": "2026-11-20 to 2026-11-26",
      "provenance": "Persisted risk assessment history",
      "is_demo_fixture": true,
      "frames": [
        {
          "id": "replay-JK-SGR-01-flood-f0",
          "timestamp": "2026-11-20T12:00:00Z",
          "phase_label": "T+0 • 2026-11-20 12:00 UTC",
          "primary_metric_label": "Risk Score",
          "primary_metric_value": "85%",
          "secondary_metric_label": "Confidence",
          "secondary_metric_value": "88%",
          "alert_tier": "High Risk",
          "risk_class": "high",
          "score": 0.85,
          "confidence": 0.88,
          "summary": "flood risk assessed at high level (88% confidence)."
        }
      ]
    }
  ]
}
```

Frames are ordered chronologically (oldest first) for playback. Each hazard
pathway (flood, avalanche) is returned as a separate replay event — pathways
are never blended.

## Role Policy

Same as other risk-read endpoints: `viewer`, `district_operator`, or `admin`.
Read-only — no mutation, no alert creation, no official-warning creation.

## Frontend Integration

`frontend/src/pages/ReplayPage.tsx` fetches `GET /risk/replay` on mount and:

- Shows a "Live Backend History" badge when data comes from the backend.
- Falls back to `MOCK_REPLAY_EVENTS` (clearly labeled "Sample Reconstruction")
  when the backend is unavailable or returns no events.
- Displays an explicit error message and retry button on API failure.
- Never presents sample reconstructions as live telemetry.

## Implementation

- Backend: `backend/app/api/routes/risk.py` (`GET /risk/replay`)
- Backend service: `backend/app/services/risk_service.py` (`RiskService.get_replay_events`)
- Backend schema: `backend/app/schemas/risk.py` (`ReplayFrameContract`, `ReplayEventContract`, `ReplayEventsResponse`)
- Frontend API: `frontend/src/api/risk.ts` (`fetchReplayEvents`)
- Frontend mapper: `frontend/src/api/mappers.ts` (`mapReplayEventToHistoricalEvent`)
- Frontend page: `frontend/src/pages/ReplayPage.tsx`
