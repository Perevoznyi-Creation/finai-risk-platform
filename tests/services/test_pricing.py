import pandas as pd
import pytest

from app.domain.metrics import compute_max_drawdown, compute_returns, compute_volatility
from app.services import risk_service


def test_get_risk_metrics_returns_computed_values(monkeypatch: pytest.MonkeyPatch) -> None:
    df = pd.DataFrame({"Close": [100.0, 110.0, 99.0, 105.0]})
    monkeypatch.setattr(risk_service, "fetch_history", lambda *_: df)

    result = risk_service.get_risk_metrics("AAPL", 4)

    returns = compute_returns(df)
    assert result["volatility"] == pytest.approx(compute_volatility(returns))
    assert result["max_drawdown"] == pytest.approx(compute_max_drawdown(df))
    assert result["mean_return"] == pytest.approx(float(returns.mean()))


def test_get_risk_profile_uses_classifier(monkeypatch: pytest.MonkeyPatch) -> None:
    df = pd.DataFrame({"Close": [100.0, 120.0, 108.0, 115.0]})
    monkeypatch.setattr(risk_service, "fetch_history", lambda *_: df)

    captured: dict[str, float] = {}

    def fake_classify(volatility: float, max_drawdown: float) -> str:
        captured["volatility"] = volatility
        captured["max_drawdown"] = max_drawdown
        return "MEDIUM"

    monkeypatch.setattr(risk_service, "classify_risk", fake_classify)

    result = risk_service.get_risk_profile("AAPL", 4)

    assert result["risk_level"] == "MEDIUM"
    assert result["volatility"] == pytest.approx(captured["volatility"])
    assert result["max_drawdown"] == pytest.approx(captured["max_drawdown"])

