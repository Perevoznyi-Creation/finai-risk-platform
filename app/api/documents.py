"""Documents API — upload and ingest financial documents for RAG."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.repositories.session import get_session
from app.schemas.errors import ErrorResponse
from app.services.document_service import ingest_document

router = APIRouter()

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class DocumentUploadResponse(BaseModel):
    """Response returned after a successful document upload."""

    document_id: int = Field(description="ID of the stored document.")
    filename: str = Field(description="Original filename.")
    chunk_count: int = Field(description="Number of text chunks embedded and stored.")
    message: str = Field(description="Human-readable confirmation.")


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def upload_document(
    file: UploadFile,
    session: Session = Depends(get_session),
) -> DocumentUploadResponse:
    """Upload a PDF or text document and ingest it for RAG queries.

    The file is extracted, split into 500-character overlapping chunks,
    embedded with ``all-MiniLM-L6-v2``, and stored in PostgreSQL.

    Args:
        file: Uploaded file (.pdf, .txt, or .md).
        session: Injected database session.

    Returns:
        Document ID, filename, and number of chunks stored.

    Raises:
        HTTPException: 400 for unsupported file type or empty PDF.
        HTTPException: 413 if the file exceeds 10 MB.
        HTTPException: 500 on unexpected ingestion failure.
    """
    file_bytes = await file.read()

    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {_MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = file.filename or "upload"

    try:
        document_id, chunk_count = ingest_document(
            filename=filename,
            file_bytes=file_bytes,
            session=session,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}") from e

    return DocumentUploadResponse(
        document_id=document_id,
        filename=filename,
        chunk_count=chunk_count,
        message=f"Document ingested successfully into {chunk_count} chunks.",
    )
