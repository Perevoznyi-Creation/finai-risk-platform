# FinAI Risk Platform

FastAPI backend for market data retrieval and basic risk analytics.

## Overview

FinAI Risk Platform provides REST endpoints for:

- Latest asset price lookup
- Historical close-price retrieval
- Risk metric computation (`volatility`, `max_drawdown`, `mean_return`)
- Risk profile classification (`LOW`, `MEDIUM`, `HIGH`) via:
  - Rule-based scoring (`mode=rule`, default)
  - ML prediction (`mode=ml`) when model artifacts are available

Market data is fetched from Yahoo Finance via `yfinance`.

## Requirements

- Python `>=3.12,<3.15`
- Poetry

## Installation

```bash
poetry install
```

## Run API

```bash
poetry run uvicorn app.main:app --reload
```

- Base URL: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Request Validation Rules

- `symbol` path param:
  - 1-10 chars
  - Regex: `^[A-Za-z][A-Za-z0-9.-]{0,9}$`
- `days` query param:
  - Integer in range `1..3650`
- `mode` query param (`/risk-profile` only):
  - `rule` (default) or `ml`

## API Endpoints

### `GET /price/{symbol}`

Returns latest close price.

```bash
curl http://127.0.0.1:8000/price/AAPL
```

Example response:

```json
{
  "symbol": "AAPL",
  "price": 213.55
}
```

### `GET /history/{symbol}?days=30`

Returns trailing daily close prices.

```bash
curl "http://127.0.0.1:8000/history/AAPL?days=30"
```

Example response:

```json
{
  "symbol": "AAPL",
  "days": 30,
  "prices": [
    { "date": "2026-02-02", "close": 209.11 }
  ]
}
```

### `GET /risk/{symbol}?days=90`

Returns computed risk metrics.

```bash
curl "http://127.0.0.1:8000/risk/AAPL?days=90"
```

Example response:

```json
{
  "symbol": "AAPL",
  "days": 90,
  "metrics": {
    "volatility": 0.0134,
    "max_drawdown": -0.112,
    "mean_return": 0.0008
  }
}
```

### `GET /risk-profile/{symbol}?days=90&mode=rule`

Returns categorical risk profile.

```bash
curl "http://127.0.0.1:8000/risk-profile/AAPL?days=90&mode=rule"
curl "http://127.0.0.1:8000/risk-profile/AAPL?days=90&mode=ml"
```

Example response:

```json
{
  "symbol": "AAPL",
  "days": 90,
  "mode": "rule",
  "profile": {
    "volatility": 0.0134,
    "max_drawdown": -0.112,
    "risk_level": "MEDIUM"
  }
}
```

## Error Response Format

All API errors use a common envelope:

```json
{
  "error": "validation_error",
  "message": "Request validation failed.",
  "details": [
    { "field": "query.days", "message": "Input should be greater than or equal to 1" }
  ]
}
```

Possible `error` values:

- `validation_error` (422)
- `http_error` (endpoint-raised HTTP errors, e.g., 400/404)
- `internal_error` (500)

## Environment Variables

- `APP_NAME` (default: `FinAI Risk Platform`)
- `APP_ENV` (default: `dev`)
- `MODEL_PATH` (default: `artifacts/risk_model.joblib`)
- `MODEL_ENCODER_PATH` (default: `artifacts/risk_label_encoder.joblib`)

## ML Notes

- `app/ml/train.py` builds a dataset and trains a model in-process.
- `/risk-profile?mode=ml` requires model artifacts to exist at `MODEL_PATH` and `MODEL_ENCODER_PATH`.
- If artifacts are missing, the API returns `400` with:
  - `"ML model artifacts not found. Train and export a model first."`

## Development

Run tests:

```bash
poetry run pytest -q
```

Lint/type-check:

```bash
poetry run ruff check app
poetry run mypy app
```

Format:

```bash
poetry run black .
```

## Project Structure

```text
app/
  main.py
  api/
    price.py
    history.py
    risk.py
    risk_profile.py
  core/
    config.py
  services/
    pricing.py
  schemas/
    risk.py
    errors.py
  metrics/
    risk.py
  scoring/
    risk_scoring.py
  ml/
    dataset.py
    model.py
    train.py
```
