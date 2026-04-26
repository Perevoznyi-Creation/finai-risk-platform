"""Pure financial metric computations — no I/O, no dependencies on infrastructure."""

import pandas as pd


def compute_returns(df: pd.DataFrame) -> pd.Series:
    """Compute simple percentage returns from close prices.

    Args:
        df: Price DataFrame containing a ``Close`` column.

    Returns:
        Return series from ``Close.pct_change()``.
    """
    return df["Close"].pct_change()


# Backward-compatible alias preserving the original typo used in imports.
compute_resurns = compute_returns


def compute_volatility(returns: pd.Series) -> float:
    """Compute volatility from a return series.

    Args:
        returns: Series of periodic returns.

    Returns:
        Standard deviation of ``returns`` as a float.
    """
    return float(returns.std())


def compute_max_drawdown(df: pd.DataFrame) -> float:
    """Compute worst peak-to-trough drawdown from close prices.

    Args:
        df: Price DataFrame containing a ``Close`` column.

    Returns:
        Minimum drawdown value (typically negative).
    """
    cumulative_max = df["Close"].cummax()
    drawdown = (df["Close"] - cumulative_max) / cumulative_max
    return float(drawdown.min())
