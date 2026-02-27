"""Application entrypoint for the FinAI Risk Platform API.

This module creates the FastAPI application instance and mounts
API routers for price and history endpoints. It also exposes a
simple health check endpoint used by orchestration and monitoring
systems.
"""

from fastapi import FastAPI
from app.api.price import router as price_router
from app.api.history import router as history_router
from app.api.risk import router as risk_router
from app.api.risk_profile import router as risk_profile_router

app = FastAPI(title="FinAI Risk Platform")

app.include_router(price_router)
app.include_router(history_router)
app.include_router(risk_router)
app.include_router(risk_profile_router)


@app.get("/health")
def health():
    """Return service liveness status.

    Returns:
        Static JSON payload indicating the API is reachable.
    """
    return {"status": "ok"}

