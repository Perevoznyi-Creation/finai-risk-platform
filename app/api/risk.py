from fastapi import APIRouter, HTTPException
from app.schemas.errors import ErrorResponse
from app.schemas.risk import DaysQueryParam, RiskExplainResponse, RiskMetrics, RiskResponse, SymbolPathParam
from app.services.llm import explain_risk
from app.services.risk_service import get_risk_metrics
from app.domain.scoring import classify_risk

router = APIRouter()


@router.get(
    "/risk/{symbol}",
    response_model=RiskResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
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


@router.get(
    "/risk/{symbol}/explain",
    response_model=RiskExplainResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def risk_explain(symbol: SymbolPathParam, days: DaysQueryParam = 90) -> RiskExplainResponse:
    """Return risk metrics plus a plain-English LLM explanation for a ticker.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days to analyze.

    Returns:
        Response with metrics, risk level, and LLM-generated explanation.

    Raises:
        HTTPException: 404 when historical data is unavailable.
        HTTPException: 500 when the LLM call fails or API key is missing.
    """
    normalized_symbol = symbol.upper()

    try:
        raw = get_risk_metrics(normalized_symbol, days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    metrics = RiskMetrics(**raw)
    risk_level = classify_risk(metrics.volatility, metrics.max_drawdown)

    try:
        explanation = explain_risk(
            symbol=normalized_symbol,
            days=days,
            volatility=metrics.volatility,
            max_drawdown=metrics.max_drawdown,
            mean_return=metrics.mean_return,
            risk_level=risk_level,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return RiskExplainResponse(
        symbol=normalized_symbol,
        days=days,
        metrics=metrics,
        risk_level=risk_level,
        explanation=explanation,
    )
