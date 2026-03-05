from types import SimpleNamespace

import pandas as pd
import pytest

from app.services import pricing


@pytest.fixture(autouse=True)
def clear_model_cache():
    pricing._load_risk_model.cache_clear()
    yield
    pricing._load_risk_model.cache_clear()


def test_get_price_returns_latest_close(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTicker:
        def history(self, period: str) -> pd.DataFrame:
            assert period == "1d"
            return pd.DataFrame({"Close": [101.25, 103.5]})

    monkeypatch.setattr(pricing.yf, "Ticker", lambda _: FakeTicker())

    assert pricing.get_price("AAPL") == 103.5


def test_get_price_raises_when_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTicker:
        def history(self, period: str) -> pd.DataFrame:
            assert period == "1d"
            return pd.DataFrame()

    monkeypatch.setattr(pricing.yf, "Ticker", lambda _: FakeTicker())

    with pytest.raises(ValueError, match="No data found for symbol AAPL"):
        pricing.get_price("AAPL")


def test_get_price_history_returns_close_column_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeTicker:
        def history(self, period: str) -> pd.DataFrame:
            assert period == "5d"
            return pd.DataFrame(
                {
                    "Open": [1.0, 2.0],
                    "Close": [3.0, 4.0],
                    "Volume": [10, 20],
                }
            )

    monkeypatch.setattr(pricing.yf, "Ticker", lambda _: FakeTicker())

    result = pricing.get_price_history("MSFT", 5)
    assert list(result.columns) == ["Close"]
    assert result["Close"].tolist() == [3.0, 4.0]


def test_get_price_history_raises_when_no_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeTicker:
        def history(self, period: str) -> pd.DataFrame:
            assert period == "30d"
            return pd.DataFrame()

    monkeypatch.setattr(pricing.yf, "Ticker", lambda _: FakeTicker())

    with pytest.raises(ValueError, match="No historical data for symbol TSLA"):
        pricing.get_price_history("TSLA", 30)


def test_get_risk_metrics_returns_computed_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    df = pd.DataFrame({"Close": [100.0, 110.0, 99.0, 105.0]})
    monkeypatch.setattr(pricing, "get_price_history", lambda *_: df)

    result = pricing.get_risk_metrics("AAPL", 4)
    returns = pricing.compute_resurns(df)

    assert result["volatility"] == pytest.approx(pricing.compute_volatility(returns))
    assert result["max_drawdown"] == pytest.approx(pricing.compute_max_drawdown(df))
    assert result["mean_return"] == pytest.approx(float(returns.mean()))


def test_get_risk_profile_uses_classifier(monkeypatch: pytest.MonkeyPatch) -> None:
    df = pd.DataFrame({"Close": [100.0, 120.0, 108.0, 115.0]})
    monkeypatch.setattr(pricing, "get_price_history", lambda *_: df)

    captured: dict[str, float] = {}

    def fake_classify(volatility: float, max_drawdown: float) -> str:
        captured["volatility"] = volatility
        captured["max_drawdown"] = max_drawdown
        return "MEDIUM"

    monkeypatch.setattr(pricing, "classify_risk", fake_classify)

    result = pricing.get_risk_profile("AAPL", 4)

    assert result["risk_level"] == "MEDIUM"
    assert result["volatility"] == pytest.approx(captured["volatility"])
    assert result["max_drawdown"] == pytest.approx(captured["max_drawdown"])


def test_load_risk_model_returns_none_when_artifacts_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        pricing,
        "get_settings",
        lambda: SimpleNamespace(
            model_path="missing-model.joblib",
            model_encoder_path="missing-encoder.joblib",
        ),
    )
    monkeypatch.setattr(pricing.Path, "exists", lambda self: False)

    assert pricing._load_risk_model() is None


def test_load_risk_model_loads_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_model = object()
    fake_encoder = object()

    monkeypatch.setattr(
        pricing,
        "get_settings",
        lambda: SimpleNamespace(
            model_path="model.joblib",
            model_encoder_path="encoder.joblib",
        ),
    )
    monkeypatch.setattr(pricing.Path, "exists", lambda self: True)

    loaded = [fake_model, fake_encoder]
    monkeypatch.setattr(pricing.joblib, "load", lambda _: loaded.pop(0))

    risk_model = pricing._load_risk_model()

    assert risk_model is not None
    assert risk_model.model is fake_model
    assert risk_model.encoder is fake_encoder


def test_get_ml_risk_profile_raises_when_model_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    df = pd.DataFrame({"Close": [100.0, 99.0, 101.0]})
    monkeypatch.setattr(pricing, "get_price_history", lambda *_: df)
    monkeypatch.setattr(pricing, "_load_risk_model", lambda: None)

    with pytest.raises(
        ValueError,
        match="ML model artifacts not found. Train and export a model first.",
    ):
        pricing.get_ml_risk_profile("AAPL", 3)


def test_get_ml_risk_profile_returns_predicted_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    df = pd.DataFrame({"Close": [100.0, 102.0, 101.0, 104.0]})
    monkeypatch.setattr(pricing, "get_price_history", lambda *_: df)

    class FakeRiskModel:
        def predict(self, features: dict) -> str:
            assert "volatility" in features
            assert "max_drawdown" in features
            assert "mean_return" in features
            return "LOW"

    monkeypatch.setattr(pricing, "_load_risk_model", lambda: FakeRiskModel())

    result = pricing.get_ml_risk_profile("MSFT", 4)

    assert result["risk_level"] == "LOW"
    assert set(result.keys()) == {
        "volatility",
        "max_drawdown",
        "mean_return",
        "risk_level",
    }
