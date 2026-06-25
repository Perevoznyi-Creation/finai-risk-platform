# FinAI Risk Platform

FastAPI backend for financial risk metrics and ML-based risk classification.

---

## Architecture

| Container | Role |
|---|---|
| **backend** | FastAPI + uvicorn, port 8000 |
| **db** | PostgreSQL 16 |
| **migrate** | Runs `alembic upgrade head` on startup, then exits |
| **pgadmin** | pgAdmin 4 UI at `http://localhost:5050` |

```
app/
  api/            Route handlers: price, history, risk, risk_profile
  core/           Config, logging
  domain/         Risk level enums, metrics, scoring
  infrastructure/ yfinance market data client
  ml/             Dataset builder, model loader, train script
  repositories/   SQLModel DB models, session, repo classes
  schemas/        Pydantic request/response schemas
  security/       API key hashing and FastAPI dependency
  services/       Business logic (risk_service, ml_service)
alembic/versions/ DB migrations
```

All endpoints require `X-API-Key` header. Error envelope: `{ "error": "...", "message": "...", "details": [...] }`.

---

## First Setup

**Requirements:** Docker, Docker Compose, Python `>=3.12`, [Poetry](https://python-poetry.org/)

```bash
poetry install              # install local dev tools
cp .env.example .env        # edit API_KEY_SALT at minimum
poetry run poe up           # build images and start all containers
poetry run poe train        # train ML model (required for mode=ml)
```

API is available at `http://localhost:8000` — Swagger UI at `/docs`.

---

## Inspect the Database (pgAdmin)

Open `http://localhost:5050` and log in with `admin@local.dev` / `admin`.

To register the DB connection:
1. Right-click **Servers** → **Register → Server**
2. **General** tab — Name: `finai`
3. **Connection** tab:
   - Host: `db`
   - Port: `5432`
   - Username: `finai`
   - Password: `finai_secret`
   - Database: `finai`

---

## Daily Workflow

```bash
poetry run poe up           # start (rebuilds if image changed)
poetry run poe down         # stop and remove containers
poetry run poe logs         # tail backend logs

git pull && poetry run poe up   # pull changes; migrate runs automatically on restart

poetry run pytest -q            # tests
poetry run ruff check app && poetry run black .  # lint & format

# Database migrations (when models change)
poetry run alembic revision --autogenerate -m "describe change"
poetry run alembic upgrade head   # local; or restart containers to apply in Docker
```
