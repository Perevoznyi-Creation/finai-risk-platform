from fastapi import APIRouter, HTTPException
from app.services.pricing import get_risk_profile

router = APIRouter()

@router.get("/risk-profile/{symbol}")
def risk_profile(symbol: str, days: int = 90):
    """Return the rule-based risk profile for a ticker.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days used for analysis.

    Returns:
        Response object with ticker metadata and computed profile.

    Raises:
        HTTPException: 400 when pricing data is unavailable or invalid.
    """
    try:
        return {
            "symbol": symbol,
            "days": days,
            "profile": get_risk_profile(symbol, days)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
