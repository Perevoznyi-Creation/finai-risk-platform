from fastapi import APIRouter, HTTPException
from app.schemas.errors import ErrorResponse
from app.schemas.risk import DaysQueryParam, RiskMetrics, RiskResponse, SymbolPathParam
from app.services.pricing import get_risk_metrics

router = APIRouter()


@router.get(
    "/risk/{symbol}",
    response_model=RiskResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def risk(symbol: SymbolPathParam, days: DaysQueryParam = 90) -> RiskResponse:
    """Return computed risk metrics for a ticker.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days to analyze.

    Returns:
        Response object with ``symbol``, ``days``, and ``metrics``.

    Raises:
        HTTPException: 404 when historical data is unavailable.
    """
    normalized_symbol = symbol.upper()

    try:
        metrics = RiskMetrics(**get_risk_metrics(normalized_symbol, days))
        return RiskResponse(symbol=normalized_symbol, days=days, metrics=metrics)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
