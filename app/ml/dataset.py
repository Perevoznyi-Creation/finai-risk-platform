import pandas as pd
from app.services.pricing import get_price_history
from app.metrics.risk import (
    compute_resurns,
    compute_volatility,
    compute_max_drawdown,
)
from app.scoring.risk_scoring import classify_risk

def build_dataset(symbols: list[str], days: int = 180) -> pd.DataFrame:
    """Build a labeled training dataset from ticker history.

    Args:
        symbols: Ticker symbols to include.
        days: Number of trailing days used per symbol.

    Returns:
        DataFrame with engineered features and rule-based label.
    """
    rows = []

    for symbol in symbols:
        df = get_price_history(symbol, days)
        returns = compute_resurns(df)

        volatility = compute_volatility(returns)
        max_drawdown = compute_max_drawdown(df)
        mean_return = float(returns.mean())

        label = classify_risk(volatility, max_drawdown)

        rows.append({
            "symbol": symbol,
            "volatility": volatility,
            "max_drawdown": max_drawdown,
            "mean_return": mean_return,
            "label": label
        })
        
    return pd.DataFrame(rows)
