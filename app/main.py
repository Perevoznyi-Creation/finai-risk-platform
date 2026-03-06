"""Application entrypoint for the FinAI Risk Platform API.

This module creates the FastAPI application instance and mounts
API routers for price and history endpoints. It also exposes a
simple health check endpoint used by orchestration and monitoring
systems.
"""

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.api.price import router as price_router
from app.api.history import router as history_router
from app.api.risk import router as risk_router
from app.api.risk_profile import router as risk_profile_router
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.risk import HealthResponse
from app.security.api_key import require_api_key

settings = get_settings()

app = FastAPI(title=settings.app_name)

protected_dependencies = [Depends(require_api_key)]

app.include_router(price_router, dependencies=protected_dependencies)
app.include_router(history_router, dependencies=protected_dependencies)
app.include_router(risk_router, dependencies=protected_dependencies)
app.include_router(risk_profile_router, dependencies=protected_dependencies)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    """Return standardized payload for controlled HTTP exceptions."""

    message = exc.detail if isinstance(exc.detail, str) else "HTTP error."
    payload = ErrorResponse(error="http_error", message=message)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return standardized payload for input validation failures."""

    details = [
        ErrorDetail(
            field=".".join(str(item) for item in error.get("loc", [])),
            message=error.get("msg", "Invalid value."),
        )
        for error in exc.errors()
    ]
    payload = ErrorResponse(
        error="validation_error",
        message="Request validation failed.",
        details=details,
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
    """Return standardized payload for unhandled server exceptions."""

    payload = ErrorResponse(
        error="internal_error",
        message="Internal server error.",
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.get(
    "/health",
    response_model=HealthResponse,
    responses={
        500: {"model": ErrorResponse},
    },
)
def health() -> HealthResponse:
    """Return service liveness status.

    Returns:
        Static JSON payload indicating the API is reachable.
    """
    return HealthResponse(status="ok")
