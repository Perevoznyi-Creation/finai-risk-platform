from fastapi import APIRouter, HTTPException
from app.services.pricing import get_risk_metrics

router = APIRouter()

@router.get("/risk/{symbol}")
def risk(symbol: str, days: int = 90):
    """Return computed risk metrics for a ticker.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days to analyze.

    Returns:
        Response object with ``symbol``, ``days``, and ``metrics``.

    Raises:
        HTTPException: 404 when historical data is unavailable.
    """
    try:
        return {
            "symbol": symbol,
            "days": days,
            "metrics": get_risk_metrics(symbol, days)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
