# FinAI Risk Platform

AI-powered financial risk and insight backend built with FastAPI.

## Overview

FinAI Risk Platform provides REST endpoints for:
- Latest asset price lookup
- Historical price retrieval
- Risk metric computation (volatility, max drawdown, mean return)
- Rule-based risk profile classification (`LOW`, `MEDIUM`, `HIGH`)

Market data is fetched from Yahoo Finance via `yfinance`.

## Tech Stack

- Python
- FastAPI + Uvicorn
- Pandas / NumPy
- Scikit-learn
- yfinance
- Poetry for dependency management

## Project Structure

```text
app/
  main.py                  # FastAPI app entrypoint
  api/
    price.py               # /price/{symbol}
    history.py             # /history/{symbol}
    risk.py                # /risk/{symbol}
    risk_profile.py        # /risk-profile/{symbol}
  services/
    pricing.py             # Market data + risk service functions
  metrics/
    risk.py                # Returns/volatility/drawdown helpers
  scoring/
    risk_scoring.py        # Rule-based risk classification
  ml/
    dataset.py             # Feature/label dataset builder
    model.py               # RiskModel prediction wrapper
    train.py               # Local training script
```

## Prerequisites

- Python `>=3.14` (as declared in `pyproject.toml`)
- Poetry

## Installation

```bash
poetry install
```

## Run the API

```bash
poetry run uvicorn app.main:app --reload
```

Default URL:
- `http://127.0.0.1:8000`

Interactive docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

## API Endpoints

### 1. Get latest price

```http
GET /price/{symbol}
```

Example:

```bash
curl http://127.0.0.1:8000/price/AAPL
```

### 2. Get historical closes

```http
GET /history/{symbol}?days=30
```

Example:

```bash
curl "http://127.0.0.1:8000/history/AAPL?days=30"
```

### 3. Get risk metrics

```http
GET /risk/{symbol}?days=90
```

Returns:
- `volatility`
- `max_drawdown`
- `mean_return`

Example:

```bash
curl "http://127.0.0.1:8000/risk/AAPL?days=90"
```

### 4. Get rule-based risk profile

```http
GET /risk-profile/{symbol}?days=90
```

Returns:
- `volatility`
- `max_drawdown`
- `risk_level` (`LOW`, `MEDIUM`, `HIGH`)

Example:

```bash
curl "http://127.0.0.1:8000/risk-profile/AAPL?days=90"
```

## ML Training Module

Train a simple model from a small ticker universe:

```bash
poetry run python -m app.ml.train
```

Current training flow:
- Builds dataset from historical prices
- Engineers `volatility`, `max_drawdown`, `mean_return`
- Uses rule-based labels as supervision target
- Trains a scikit-learn Random Forest model

## Development

Run tests:

```bash
poetry run pytest
```

Lint and format:

```bash
poetry run ruff check .
poetry run black .
poetry run mypy app
```

## Notes

- Data availability depends on Yahoo Finance coverage for each ticker.
- Invalid or unavailable symbols return API errors (`400`/`404`, depending on endpoint).
