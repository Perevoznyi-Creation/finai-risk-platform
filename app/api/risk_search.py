"""Risk search endpoint — semantic nearest-neighbor search over stored analyses."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.repositories.risk_analysis_repo import RiskAnalysisRepository
from app.repositories.session import get_session
from app.schemas.errors import ErrorResponse
from app.schemas.risk import RiskSearchResponse, RiskSearchResult
from app.services.embeddings import embed_text

router = APIRouter()


@router.get(
    "/risk/search",
    response_model=RiskSearchResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def risk_search(
    query: str = Query(min_length=3, max_length=500, description="Natural-language search query."),
    limit: int = Query(default=5, ge=1, le=20, description="Maximum number of results."),
    session: Session = Depends(get_session),
) -> RiskSearchResponse:
    """Search stored risk analyses semantically using vector similarity.

    Embeds the query locally with ``all-MiniLM-L6-v2``, then finds the
    closest stored embeddings in PostgreSQL using pgvector cosine distance.

    Args:
        query: Natural-language query, e.g. ``"high volatility tech stocks"``.
        limit: Maximum results to return (1–20).
        session: Injected database session.

    Returns:
        Matched risk analyses ordered by semantic similarity, closest first.

    Raises:
        HTTPException: 500 on embedding failure.
    """
    try:
        query_embedding = embed_text(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}") from e

    repo = RiskAnalysisRepository(session)
    rows = repo.search_by_embedding(query_embedding, limit=limit)

    results = [
        RiskSearchResult(
            id=row.id,
            symbol=row.symbol,
            days=row.days,
            risk_level=row.risk_level.value,
            volatility=row.volatility,
            max_drawdown=row.max_drawdown,
            mean_return=row.mean_return,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]

    return RiskSearchResponse(query=query, results=results)
