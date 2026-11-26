# Core Risk API Reference

This document describes the paginated, filterable, and role-enforced REST API endpoints for locations, observations, and multi-hazard risk assessments in HIMA-RAKSHAK.

## Authentication & Authorization

Protected endpoints support:
1. **Bearer Token (JWT)**: `Authorization: Bearer <token>` obtained via `POST /auth/login`.
   - Roles: `admin`, `district_operator`, `viewer`.
2. **Internal Role Header**: `X-User-Role: admin` (legacy/service-to-service header for pilot location management).

### Access Matrix

| Endpoint | Method | Required Role |
| :--- | :--- | :--- |
| `GET /locations` | GET | Public / Any |
| `GET /locations/{id}` | GET | Public / Any |
| `POST /locations` | POST | `admin` |
| `PATCH /locations/{id}/coverage` | PATCH | `admin` |
| `GET /observations` | GET | `viewer`, `district_operator`, or `admin` |
| `GET /risk/current/{id}` | GET | `viewer`, `district_operator`, or `admin` |
| `GET /risk/history/{id}` | GET | `viewer`, `district_operator`, or `admin` |
| `GET /risk/state/{id}` | GET | `viewer`, `district_operator`, or `admin` |
| `POST /risk/assess/{id}` | POST | `district_operator` or `admin` |

---

## Standard Error Envelope

All error responses (4xx, 5xx) conform to the shared `ErrorEnvelope` schema:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request parameter validation failed.",
  "details": [
    {
      "field": "query -> page",
      "code": "greater_than_equal",
      "message": "Input should be greater than or equal to 1"
    }
  ],
  "timestamp": "2026-11-26T12:00:00Z"
}
```

---

## Endpoints

### 1. Pilot Locations

#### `GET /locations`
List and search pilot locations with pagination.

**Query Parameters:**
- `q` (string, optional): Search query matching location ID, name, or admin unit.
- `hazard_type` (string, optional): Filter by supported hazard (`flood`, `avalanche`).
- `coverage_status` (string, optional): Filter by coverage (`supported`, `partial`, `unsupported`).
- `page` (integer, default `1`, ge `1`): 1-based page number.
- `page_size` (integer, default `20`, ge `1`, le `100`): Items per page.

**Response (200 OK):**
```json
{
  "total": 5,
  "items": [
    {
      "location_id": "JK-SGR-01",
      "name": "Srinagar — Dal Lake Basin",
      "admin_unit": "Srinagar District, J&K",
      "latitude": 34.0837,
      "longitude": 74.7973,
      "supported_hazards": ["flood"],
      "coverage_status": "supported",
      "coverage_note": "Operational pilot gauge station",
      "is_demo_fixture": true,
      "provenance": "official:cwc-pilot"
    }
  ],
  "pagination": {
    "total": 5,
    "page": 1,
    "page_size": 20,
    "has_next": false
  }
}
```

---

### 2. Environmental Observations

#### `GET /observations`
List environmental observations for a specific location.

**Query Parameters:**
- `location_id` (string, required): Pilot location identifier (e.g. `JK-SGR-01`).
- `metric` (string, optional): One of `rain_mm`, `river_level_m`, `snow_depth_cm`, `wind_kmh`, `temp_c`.
- `since` (ISO 8601 string, optional): Filter observations on or after this timestamp.
- `until` (ISO 8601 string, optional): Filter observations on or before this timestamp.
- `page` (integer, default `1`, ge `1`): 1-based page number.
- `page_size` (integer, default `20`, ge `1`, le `100`): Items per page.

**Response (200 OK):**
```json
{
  "total": 1,
  "items": [
    {
      "observation_id": "obs-001",
      "location_id": "JK-SGR-01",
      "source_id": "src-cwc-01",
      "observed_at": "2026-11-26T12:00:00Z",
      "metric": "rain_mm",
      "value": 24.5,
      "unit": "mm",
      "is_demo_fixture": true
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "page_size": 20,
    "has_next": false
  }
}
```

---

### 3. Risk Assessments

#### `GET /risk/current/{location_id}`
Returns the latest persisted risk assessment for each hazard pathway at the location. Hazard outputs remain distinct and are never blended.

**Response (200 OK):**
```json
{
  "flood": {
    "risk_id": "risk-flood-01",
    "location_id": "JK-SGR-01",
    "hazard_type": "flood",
    "risk_class": "high",
    "score": 0.85,
    "confidence": 0.90,
    "lead_time_hours": 24,
    "freshness": "fresh",
    "prediction_status": "ready",
    "readiness_reason": null,
    "assessed_at": "2026-11-26T12:00:00Z",
    "model_version": "flood-baseline-v1",
    "provenance": {
      "source_id": "src-cwc-01",
      "source_name": "Central Water Commission",
      "licence": "GODL",
      "is_demo_fixture": true,
      "ingested_at": "2026-11-26T12:05:00Z"
    }
  },
  "avalanche": null
}
```

#### `GET /risk/history/{location_id}`
Paginated historical log of risk assessments for auditability and trend tracking.

**Query Parameters:**
- `hazard_type` (string, optional): `flood` or `avalanche`.
- `since` (ISO 8601 string, optional): Timestamp lower bound.
- `page` (integer, default `1`, ge `1`): 1-based page number.
- `page_size` (integer, default `20`, ge `1`, le `100`): Items per page.

#### `GET /risk/state/{location_id}`
Returns the compiled multi-hazard spatial state for the location, with `highest_risk_class` and `primary_hazard` resolved deterministically while preserving separate hazard pathways.

#### `POST /risk/assess/{location_id}`
Triggers the multi-hazard risk assessment pipeline for `location_id` using persisted observations up to `cutoff_at` (defaults to current UTC time). Executes separate flood and avalanche feature extraction and `RiskOrchestrator` pathways, persists results, and returns the compiled `LocationRiskState`.

- **Required Role:** `district_operator` or `admin`
- **Optional Request Body:**
  ```json
  {
    "cutoff_at": "2026-11-26T12:00:00Z"
  }
  ```
- **Responses:** `200 OK` (`LocationRiskState`), `401 Unauthorized`, `403 Forbidden`, `404 Not Found` (unknown `location_id`).
