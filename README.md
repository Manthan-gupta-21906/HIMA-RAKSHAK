# HIMA-RAKSHAK

**Multi-Hazard Risk Intelligence & Early-Warning Decision-Support System for Jammu & Kashmir (Team 12 — PS-12)**

## Product Contract
- **Separate Hazard Pathways:** Independent Flood and Avalanche engines feeding a shared spatial risk state.
- **Provenance & Uncertainty:** Every assessment tracks confidence, data freshness, source provenance, and lead time.
- **Exposure & Priority:** Connects hazard outputs to settlements, roads, homes, and critical services to prioritize attention.
- **Authoritative Warnings:** Official CWC/IMD and DGRE warnings remain authoritative and read-only. This system supports preparedness decisions and does not issue autonomous evacuation or road-closure orders.

## Tech Stack
- **Backend:** Python, FastAPI, Pydantic
- **Database:** PostgreSQL + PostGIS
- **ML & Geospatial:** scikit-learn, Pandas, GeoPandas, Rasterio, Shapely
- **Frontend:** React, TypeScript, Leaflet

## Local Setup (Backend)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Running Checks
```bash
cd backend
ruff check .
pytest
```

## API Endpoint Policy
- **Public (unauthenticated):** `GET /health`, `POST /auth/login`
- **Authenticated (`viewer`, `district_operator`, `admin`):** `GET /auth/me`, `GET /locations*`, `GET /sources*`, `GET /observations`, `GET /risk/*`, `GET /warnings*`
- **Operator / Admin (`district_operator`, `admin`):** `POST /warnings*`
- **Admin only (`admin`):** `POST /locations`, `PATCH /locations/{location_id}/coverage`, `POST /sources*`
