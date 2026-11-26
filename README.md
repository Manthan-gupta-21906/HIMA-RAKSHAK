# HIMA-RAKSHAK

**Multi-Hazard Risk Intelligence & Early-Warning Decision-Support System for Jammu & Kashmir (Team 12 — PS-12)**

---

## 1. Project Overview & Architecture

### Overview
**HIMA-RAKSHAK** is an operational decision-support system (DDSS) engineered for high-altitude hazard intelligence across Jammu & Kashmir. The system continuously evaluates independent flood and avalanche risk pathways, integrates real-time environmental telemetry, correlates hazard footprints with vulnerable civilian exposure, and presents actionable situational awareness for disaster management authorities (SDMA/DDMA).

### Core Product Principles
- **Separate Hazard Pathways:** Flood and Avalanche risk engines operate independently and are never averaged or blended into an arbitrary single composite score.
- **Spatial Exposure & Priority:** Connects multi-hazard spatial footprints to settlements, residential structures, transport arteries (NH-44), and critical lifelines (hospitals, shelters, power, telecom) to rank priority attention.
- **Provenance, Uncertainty & Freshness:** Every evaluation tracks data confidence, freshness decay, sensor source provenance, and forecast lead time.
- **Authoritative Warning Preservation:** Official bulletins from IMD, CWC, and DGRE are ingested as authoritative, immutable, and read-only.
- **Strict Ground-Truth Policy:** Where verified disaster labels are absent, the system flags `indicative_screening` or `unsupported` rather than claiming synthetic accuracy.

### System Architecture Diagram

```mermaid
graph TD
    subgraph DataSources["Data Sources & Ingestion"]
        IMD["IMD Weather Telemetry<br/>(Rainfall, Wind, Temp)"]
        CWC["CWC River Stages<br/>(Jhelum Basin Gauges)"]
        DGRE["DGRE Avalanche Bulletins<br/>(Authoritative Read-Only)"]
        GIS["Vector & Raster Layers<br/>(DEM, Catchments, NH-44)"]
        CSV["CSV & Field Observations<br/>(Ground Sensor Telemetry)"]
    end

    subgraph BackendCore["FastAPI Backend Core (Port 8000)"]
        Ingest["Ingestion & Validation Engine<br/>(Idempotency, Normalization)"]
        AuthService["Auth & RBAC Service<br/>(JWT, Role Guard)"]
        
        subgraph Engines["Independent Hazard Engines"]
            FloodEng["Flood Hazard Engine<br/>(Hydrological Features, Antecedent Rain)"]
            AvEng["Avalanche Hazard Engine<br/>(Snowpack Readiness, Terrain Screening)"]
        end

        ExposureSvc["Spatial Exposure & Priority Engine<br/>(Settlements, Roads, Lifelines)"]
        RiskOrch["Multi-Hazard Risk Orchestrator<br/>(State Compilation, Uncertainty, Provenance)"]
    end

    subgraph Storage["Persistence Layer"]
        Postgres[("PostgreSQL 16 + PostGIS<br/>(Port 5432)")]
    end

    subgraph Presentation["React Frontend (Port 5173)"]
        Dashboard["Operator Command Dashboard<br/>(Situational Overview)"]
        MapModule["Interactive GIS Leaflet Map<br/>(Hazard Layers, Buffer Zones)"]
        WarnPanel["Authoritative Warnings Panel<br/>(CWC / DGRE Feeds)"]
        ReplayObs["Historical Replay & Field Logs<br/>(Timeline Scrubbing, Sensor Logs)"]
    end

    DataSources --> Ingest
    Ingest --> Postgres
    Postgres <--> Engines
    Engines --> RiskOrch
    GIS --> ExposureSvc
    RiskOrch <--> ExposureSvc
    ExposureSvc --> Postgres
    
    AuthService <--> Postgres
    RiskOrch --> BackendCore
    BackendCore -->|REST / JSON API| Presentation
```

---

## 2. Prerequisites

Ensure the following tools are installed on your host machine:

| Requirement | Docker Startup (Recommended) | Manual Startup |
| :--- | :--- | :--- |
| **Docker** | Docker Engine `20.10+` & Docker Compose `v2.0+` | Not required (or Docker for DB only) |
| **Python** | Bundled in container | Python `3.11+` (Python `3.12` recommended) |
| **Node.js** | Bundled in container | Node.js `18.x`, `20.x`, or `22.x` & `npm` |
| **Database** | Handled via `docker-compose.yml` | PostgreSQL `14+` with PostGIS extension (or SQLite for lightweight tests) |

---

## 3. Docker Setup (Judge Quickstart)

The simplest and fastest way to evaluate the complete stack is via Docker Compose.

### Step 1: Clone & Configure Environment
```bash
# Navigate to project root
cd HIMA-RAKSHAK

# Copy the environment template
cp .env.example .env
```
*(On Windows PowerShell, run: `copy .env.example .env`)*

### Step 2: Build and Start Services
```bash
docker compose up --build
```

### Step 3: Access the Running System
Once started, the following services will be available:
- **Frontend Command Center:** [http://localhost:5173](http://localhost:5173)
- **Backend REST API:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostGIS Spatial Database:** `localhost:5432` (`hima_rakshak`)

### Stopping the Services
```bash
# Graceful stop
docker compose down

# Stop and wipe database volume for a clean state
docker compose down -v
```

---

## 4. Manual Frontend & Backend Setup

For step-by-step local development without Docker:

### Step 1: Database Setup
You can either run a standalone PostgreSQL/PostGIS instance or launch only the database container:
```bash
# Run database via Docker
docker compose up -d db
```
Alternatively, configure a local PostgreSQL instance with the PostGIS extension enabled:
```sql
CREATE DATABASE hima_rakshak;
\c hima_rakshak;
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Step 2: Backend Setup (FastAPI)
```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python virtual environment
# On Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate

# On Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install backend dependencies in editable mode with dev tools
pip install -e ".[dev]"

# 4. Run database migrations
alembic upgrade head

# 5. Start the FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*The API is now running at [http://localhost:8000](http://localhost:8000).*

### Step 3: Frontend Setup (React + Vite)
In a new terminal window:
```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite development server
npm run dev
```
*The web interface is now accessible at [http://localhost:5173](http://localhost:5173).*

---

## 5. Environment Variable Instructions

All environment settings are loaded from the root `.env` file (copied from `.env.example`).

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `HIMA-RAKSHAK` | Descriptive name of the service |
| `APP_ENV` | `development` | Deployment environment (`development`, `staging`, `production`) |
| `APP_VERSION` | `0.1.0` | Semantic version string |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `DATABASE_URL` | `postgresql+psycopg://hima:hima@localhost:5432/hima_rakshak` | SQLAlchemy connection string (supports SQLite: `sqlite:///./test.db`) |
| `POSTGRES_USER` | `hima_user` | PostgreSQL superuser for Docker Compose service |
| `POSTGRES_PASSWORD` | `change_me_local_only` | PostgreSQL user password |
| `POSTGRES_DB` | `hima_rakshak` | PostgreSQL primary database name |
| `JWT_SECRET_KEY` | `change-me-in-local-env` | Cryptographic key used to sign HS256 authentication tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Lifespan of issued access tokens in minutes |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend base URL consumed by the React/Vite frontend |

---

## 6. Demo Credentials & User Roles

The system includes pre-seeded demo accounts and role-based access control (RBAC).

| Role | Username / Identifier | Password | Access & Capabilities |
| :--- | :--- | :--- | :--- |
| **DDMA Operator** *(Primary)* | `operator`<br>*(or `ops.srinagar@jk-ddma.gov.in`)* | `operator1234` | Full control-room triage, field observations, warning ingestion, and historical replay |
| **System Admin** | `admin`<br>*(or `admin@jk-ddma.gov.in`)* | `admin1234` | Location management, data source registry, spatial layer management |
| **SDMA Viewer** | `viewer`<br>*(or `viewer@jk-ddma.gov.in`)* | `viewer1234` | Read-only advisory monitoring, situation logs, and executive risk inspection |

> **Judge Tip:** On the login screen (`http://localhost:5173`), click the **"Use Demo Credentials"** button to automatically pre-populate the active operator login. In offline/mock mode, the frontend seamlessly supports the operator profile with local session persistence.

---

## 7. API Documentation & Interactive Endpoints

FastAPI automatically generates interactive OpenAPI/Swagger schemas:

- **Swagger UI (Interactive API Explorer):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc (Alternative Spec Reader):** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Raw OpenAPI JSON Spec:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- **Comprehensive API Guide:** Located in [`docs/api/core_risk_api.md`](docs/api/core_risk_api.md)

### Key Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check and runtime metadata |
| `POST` | `/auth/login` | Authenticate with username and password, returns JWT |
| `GET` | `/auth/me` | Fetch authenticated profile and assigned role |
| `GET` | `/locations` | List/search J&K pilot locations with hazard & coverage filters |
| `GET` | `/sources` | Registry of authoritative telemetry providers (IMD, CWC, DGRE) |
| `GET` | `/observations` | Query environmental observations (rain, snow, river stage, wind) |
| `GET` | `/risk/current/{id}` | Real-time multi-hazard risk state for a specific location |
| `GET` | `/risk/history/{id}` | Audit trail and historical risk progression |
| `GET` | `/warnings` | List authoritative official bulletins from CWC/DGRE/IMD |
| `POST` | `/warnings/import-fixtures` | Bulk-import deterministic demo warning bulletins (Operator/Admin) |

### API Endpoint Policy
- **Public (unauthenticated):** `GET /health`, `POST /auth/login`
- **Authenticated (`viewer`, `district_operator`, `admin`):** `GET /auth/me`, `GET /locations*`, `GET /sources*`, `GET /observations`, `GET /risk/*`, `GET /warnings*`
- **Operator / Admin (`district_operator`, `admin`):** `POST /warnings*`
- **Admin only (`admin`):** `POST /locations`, `PATCH /locations/{location_id}/coverage`, `POST /sources*`

---

## 8. Seed-Data & Ingestion Instructions

The repository includes deterministic fixtures for pilot demonstration without requiring live API keys.

### 1. Pilot Locations (Auto-Seeded)
Pilot hubs in Jammu & Kashmir are automatically seeded into the system repository on startup:
- `JK-SGR-01`: **Srinagar — Jhelum Floodplain** *(Flood pathway; supported coverage)*
- `JK-GUL-01`: **Gulmarg — Affarwat Ridge** *(Avalanche pathway; indicative screening)*
- `JK-BAN-01`: **Banihal — NH-44 Corridor** *(Dual-hazard; road exposure corridor)*
- `JK-DRS-01`: **Drass — Zojila High Pass** *(High-altitude pass; unsupported screening)*

### 2. Demo Users (Auto-Seeded)
Demo users (`admin`, `operator`, `viewer`) are automatically created idempotently upon the first call to `/auth/login`.

### 3. Ingesting Sample Environmental Observations
Synthetic observations are provided in [`data/fixtures/sample_observations.csv`](data/fixtures/sample_observations.csv). To load them into the database:
```python
# Launch Python interactive session in backend
cd backend
python -c "
from app.db.session import create_db_engine, get_session_factory
from app.repositories.observation_repository import ObservationRepository
from app.repositories.source_repository import SourceRepository
from app.services.ingestion_service import IngestionService
from pathlib import Path

db = get_session_factory(create_db_engine())()
svc = IngestionService(ObservationRepository(db), SourceRepository(db))
result = svc.ingest_csv(Path('../data/fixtures/sample_observations.csv'), source_id='src-cwc-01')
db.commit()
print(f'Ingested: {result.inserted} rows, Duplicates skipped: {result.skipped_duplicates}')
"
```

### 4. Ingesting Official Warning Bulletins
Trigger the pre-packaged sample warnings via HTTP:
```bash
curl -X POST "http://localhost:8000/warnings/import-fixtures" \
  -H "Authorization: Bearer <OPERATOR_JWT_TOKEN>"
```

### 5. Spatial GIS Layers
GeoJSON vector boundaries and catchment buffer zones are catalogued in `data/layers/` (`pilot_coverage_zones.geojson` and `data/layers/exposure/`).

---

## 9. Test Commands & Quality Checks

Run the automated test suites to verify backend integrity, anti-leakage contracts, and frontend components:

### Backend Tests & Code Quality
```bash
cd backend

# Run all pytest suites (unit, integration, schemas, geospatial, ML baseline)
pytest -v

# Run Ruff linter and code formatter checks
ruff check .
```

### Frontend Tests & Type Validation
```bash
cd frontend

# Run unit and component test suite (Vitest + React Testing Library)
npm test

# Run TypeScript type check
npm run typecheck

# Verify production production bundle build
npm run build
```

---

## 10. Known Limitations & Operational Boundary

In compliance with disaster management engineering safety standards:

1. **Independent Pathway Invariance:** Flood and avalanche risk scores are never blended into a single composite number. Each hazard preserves its unique physical dynamics, lead times, and spatial characteristics.
2. **Strict Ground-Truth Validation Policy:** In accordance with the project feasibility audit ([`reports/avalanche/feasibility.md`](reports/avalanche/feasibility.md) and [`reports/flood/DATA_READINESS.md`](reports/flood/DATA_READINESS.md)), statistical validation claims are strictly withheld when certified disaster incident logs are unavailable. Stations with sparse telemetry default to `indicative_screening` or `unsupported`.
3. **Synthetic Demo Fixtures:** Datasets under `data/fixtures/` are synthetic samples created for offline demonstration and testing; they do not represent live operational feeds from IMD, CWC, or DGRE.
4. **No Autonomous Executive Orders:** The system is an advisory Decision-Support System (DDSS). Official IMD/CWC/DGRE bulletins remain authoritative and read-only. HIMA-RAKSHAK does not issue autonomous or binding evacuation or highway-closure mandates.
5. **Geographic Pilot Boundary:** High-resolution spatial exposure models are calibrated specifically for Jammu & Kashmir pilot sectors (Srinagar, Gulmarg, Banihal NH-44, and Drass corridors).

  

