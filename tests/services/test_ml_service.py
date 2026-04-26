from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from app.services import ml_service


@pytest.fixture(autouse=True)
def clear_model_cache():
    ml_service._load_risk_model.cache_clear()
    yield
    ml_service._load_risk_model.cache_clear()


def test_load_risk_model_returns_none_when_artifacts_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ml_service,
        "get_settings",
        lambda: SimpleNamespace(
            model_path="missing-model.joblib",
            model_encoder_path="missing-encoder.joblib",
        ),
    )
    monkeypatch.setattr(ml_service.Path, "exists", lambda self: False)

    assert ml_service._load_risk_model() is None


def test_load_risk_model_loads_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_model = object()
    fake_encoder = object()

    monkeypatch.setattr(
        ml_service,
        "get_settings",
        lambda: SimpleNamespace(
            model_path="model.joblib",
            model_encoder_path="encoder.joblib",
        ),
    )
    monkeypatch.setattr(ml_service.Path, "exists", lambda self: True)

    loaded = [fake_model, fake_encoder]
    monkeypatch.setattr(ml_service.joblib, "load", lambda _: loaded.pop(0))

    risk_model = ml_service._load_risk_model()

    assert risk_model is not None
    assert risk_model.model is fake_model
    assert risk_model.encoder is fake_encoder


def test_get_ml_risk_profile_raises_when_model_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    df = pd.DataFrame({"Close": [100.0, 99.0, 101.0]})
    monkeypatch.setattr(ml_service, "fetch_history", lambda *_: df)
    monkeypatch.setattr(ml_service, "_load_risk_model", lambda: None)

    with pytest.raises(
        ValueError,
        match="ML model artifacts not found. Train and export a model first.",
    ):
        ml_service.get_ml_risk_profile("AAPL", 3)


def test_get_ml_risk_profile_returns_predicted_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    df = pd.DataFrame({"Close": [100.0, 102.0, 101.0, 104.0]})
    monkeypatch.setattr(ml_service, "fetch_history", lambda *_: df)

    class FakeRiskModel:
        def predict(self, features: dict) -> str:
            assert "volatility" in features
            assert "max_drawdown" in features
            assert "mean_return" in features
            return "LOW"

    monkeypatch.setattr(ml_service, "_load_risk_model", lambda: FakeRiskModel())

    result = ml_service.get_ml_risk_profile("MSFT", 4)

    assert result["risk_level"] == "LOW"
    assert set(result.keys()) == {"volatility", "max_drawdown", "mean_return", "risk_level"}
