from fastapi import APIRouter, HTTPException
from app.services.pricing import get_risk_metrics

router = APIRouter()

@router.get("/risk/{symbol}")
def risk(symbol: str, days: int = 90):
    """Return risk metrics for an asset based on historical prices.

    Parameters:
        symbol (str): Asset ticker symbol.
        days (int): Number of past days to analyze (default: 30).
    Returns:
        dict: JSON object containing `symbol`, `days`, `volatility`, and
                `max_drawdown` metrics.
    Raises:
        HTTPException: 404 when no historical data is available.
    """
    try:
        return {
            "symbol": symbol,
            "days": days,
            "metrics": get_risk_metrics(symbol, days)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))