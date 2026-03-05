import asyncio
import json

import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from app.api import history as history_api
from app.api import price as price_api
from app.api import risk as risk_api
from app.api import risk_profile as risk_profile_api
from app.main import (
    health,
    http_exception_handler,
    request_validation_exception_handler,
    unhandled_exception_handler,
)
from app.schemas.risk import RiskProfileMode


def test_health_returns_ok() -> None:
    result = health()
    assert result.status == "ok"


def test_price_success_uppercases_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    def fake_get_price(symbol: str) -> float:
        captured["symbol"] = symbol
        return 123.45

    monkeypatch.setattr(price_api, "get_price", fake_get_price)

    result = price_api.price("aapl")

    assert result.symbol == "AAPL"
    assert result.price == 123.45
    assert captured["symbol"] == "AAPL"


def test_price_value_error_maps_to_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        price_api,
        "get_price",
        lambda _: (_ for _ in ()).throw(ValueError("No data found for symbol AAPL")),
    )

    with pytest.raises(HTTPException) as exc:
        price_api.price("aapl")

    assert exc.value.status_code == 404
    assert exc.value.detail == "No data found for symbol AAPL"


def test_history_success_serializes_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    index = pd.to_datetime(["2026-02-01", "2026-02-02"])
    df = pd.DataFrame({"Close": [201.0, 202.5]}, index=index)
    monkeypatch.setattr(history_api, "get_price_history", lambda *_: df)

    result = history_api.history("msft", days=2)

    assert result.symbol == "MSFT"
    assert result.days == 2
    assert [point.date.isoformat() for point in result.prices] == [
        "2026-02-01",
        "2026-02-02",
    ]
    assert [point.close for point in result.prices] == [201.0, 202.5]


def test_risk_success_returns_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        risk_api,
        "get_risk_metrics",
        lambda *_: {
            "volatility": 0.0123,
            "max_drawdown": -0.15,
            "mean_return": 0.001,
        },
    )

    result = risk_api.risk("tsla", days=90)

    assert result.symbol == "TSLA"
    assert result.days == 90
    assert result.metrics.volatility == 0.0123
    assert result.metrics.max_drawdown == -0.15
    assert result.metrics.mean_return == 0.001


def test_risk_profile_rule_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, int | str] = {}

    def fake_rule_profile(symbol: str, days: int) -> dict:
        captured["symbol"] = symbol
        captured["days"] = days
        return {
            "volatility": 0.01,
            "max_drawdown": -0.05,
            "risk_level": "LOW",
        }

    monkeypatch.setattr(risk_profile_api, "get_risk_profile", fake_rule_profile)

    result = risk_profile_api.risk_profile(
        symbol="aapl",
        days=30,
        mode=RiskProfileMode.rule,
    )

    assert result.symbol == "AAPL"
    assert result.days == 30
    assert result.mode == RiskProfileMode.rule
    assert result.profile.risk_level.value == "LOW"
    assert captured == {"symbol": "AAPL", "days": 30}


def test_risk_profile_ml_mode_uses_ml_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        risk_profile_api,
        "get_ml_risk_profile",
        lambda *_: {
            "volatility": 0.02,
            "max_drawdown": -0.2,
            "mean_return": 0.0007,
            "risk_level": "MEDIUM",
        },
    )

    result = risk_profile_api.risk_profile(
        symbol="amzn",
        days=45,
        mode=RiskProfileMode.ml,
    )

    assert result.symbol == "AMZN"
    assert result.days == 45
    assert result.mode == RiskProfileMode.ml
    assert result.profile.risk_level.value == "MEDIUM"


def test_risk_profile_ml_value_error_maps_to_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        risk_profile_api,
        "get_ml_risk_profile",
        lambda *_: (_ for _ in ()).throw(
            ValueError("ML model artifacts not found. Train and export a model first.")
        ),
    )

    with pytest.raises(HTTPException) as exc:
        risk_profile_api.risk_profile("meta", mode=RiskProfileMode.ml)

    assert exc.value.status_code == 400
    assert exc.value.detail == "ML model artifacts not found. Train and export a model first."


def test_risk_profile_rule_value_error_maps_to_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        risk_profile_api,
        "get_risk_profile",
        lambda *_: (_ for _ in ()).throw(ValueError("No historical data for symbol META")),
    )

    with pytest.raises(HTTPException) as exc:
        risk_profile_api.risk_profile("meta", mode=RiskProfileMode.rule)

    assert exc.value.status_code == 404
    assert exc.value.detail == "No historical data for symbol META"


def test_http_exception_handler_payload() -> None:
    response = asyncio.run(
        http_exception_handler(None, HTTPException(status_code=404, detail="Missing"))
    )
    body = json.loads(response.body)

    assert response.status_code == 404
    assert body == {"error": "http_error", "message": "Missing", "details": None}


def test_request_validation_exception_handler_payload() -> None:
    exc = RequestValidationError(
        errors=[
            {"loc": ("path", "symbol"), "msg": "Invalid symbol", "type": "value_error"}
        ]
    )

    response = asyncio.run(request_validation_exception_handler(None, exc))
    body = json.loads(response.body)

    assert response.status_code == 422
    assert body["error"] == "validation_error"
    assert body["message"] == "Request validation failed."
    assert body["details"] == [{"field": "path.symbol", "message": "Invalid symbol"}]


def test_unhandled_exception_handler_payload() -> None:
    response = asyncio.run(unhandled_exception_handler(None, RuntimeError("boom")))
    body = json.loads(response.body)

    assert response.status_code == 500
    assert body == {
        "error": "internal_error",
        "message": "Internal server error.",
        "details": None,
    }
