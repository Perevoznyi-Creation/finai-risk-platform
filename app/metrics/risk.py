"""Risk and metrics helper functions.

This module contains utilities for computing basic risk metrics
from price data frames used elsewhere in the application.
"""

import pandas as pd


def compute_resurns(df: pd.DataFrame) -> pd.Series:
    """Compute simple percentage returns from close prices.

    The function name intentionally keeps the existing typo for
    backward compatibility with current imports.

    Args:
        df: Price DataFrame containing a ``Close`` column.

    Returns:
        Return series from ``Close.pct_change()``.
    """

    return df['Close'].pct_change()

def compute_volatility(returns: pd.Series) -> float:
    """Compute volatility from a return series.

    Args:
        returns: Series of periodic returns.

    Returns:
        Standard deviation of ``returns`` as a float.
    """
    return float(returns.std())

def compute_max_drawdown(df: pd.DataFrame) -> float:
    """Compute worst drawdown from peak close prices.

    Args:
        df: Price DataFrame containing a ``Close`` column.

    Returns:
        Minimum drawdown value (typically negative).
    """
    cumulative_max = df['Close'].cummax()
    drawdown = (df["Close"] - cumulative_max) / cumulative_max

    return float(drawdown.min())

