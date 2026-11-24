# HIMA-RAKSHAK

Multi-hazard flood & avalanche decision-support prototype for Jammu & Kashmir.

> **Decision-support only** — complements official warnings (IMD, CWC, DGRE), not a replacement.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI |
| Frontend | React · TypeScript · Vite |
| Database | PostgreSQL + PostGIS |

## Quick start

```bash
cp .env.example .env

# Docker
docker compose up --build

# Or native
cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

## Checks

```bash
cd backend && ruff check . && pytest
cd frontend && npm run typecheck && npm run build
```
