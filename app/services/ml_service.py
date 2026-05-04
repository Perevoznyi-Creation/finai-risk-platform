"""ML-based risk analysis service — loads model artifacts and runs inference."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

from app.core.config import get_settings
from app.domain.metrics import compute_max_drawdown, compute_returns, compute_volatility
from app.infrastructure.market.yfinance_client import fetch_history
from app.ml.model import RiskModel

logger = logging.getLogger(__name__)


@lru_cache
def _load_risk_model() -> RiskModel | None:
    """Load and cache the ML risk model from configured artifact paths."""

    settings = get_settings()
    model_path = Path(settings.model_path)
    encoder_path = Path(settings.model_encoder_path)

    if not model_path.exists() or not encoder_path.exists():
        logger.warning(
            "ML model artifacts not found — model: %s, encoder: %s",
            model_path,
            encoder_path,
        )
        return None

    model = joblib.load(model_path)
    encoder = joblib.load(encoder_path)
    logger.info("ML risk model loaded from %s", model_path)
    return RiskModel(model=model, encoder=encoder)


def get_ml_risk_profile(symbol: str, days: int) -> dict[str, Any]:
    """Predict risk level with the trained ML model.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days used for feature extraction.

    Returns:
        Dictionary of computed features plus predicted ``risk_level``.

    Raises:
        ValueError: Model artifacts are missing — train and export a model first.
    """
    logger.debug("Running ML risk profile for %s over %d days", symbol, days)
    df = fetch_history(symbol, days)
    returns = compute_returns(df)

    features: dict[str, Any] = {
        "volatility": compute_volatility(returns),
        "max_drawdown": compute_max_drawdown(df),
        "mean_return": float(returns.mean()),
    }

    risk_model = _load_risk_model()
    if risk_model is None:
        raise ValueError(
            "ML model artifacts not found. Train and export a model first."
        )

    result = {**features, "risk_level": risk_model.predict(features)}
    logger.debug("ML risk profile for %s: %s", symbol, result["risk_level"])
    return result
