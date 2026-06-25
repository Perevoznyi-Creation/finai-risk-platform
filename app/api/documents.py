"""Documents API — upload and ingest financial documents for RAG."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.repositories.document_repo import DocumentRepository
from app.repositories.session import get_session
from app.schemas.errors import ErrorResponse
from app.services.document_service import ingest_document
from app.services.rag import answer_question

router = APIRouter()


class DocumentChatRequest(BaseModel):
    """Request payload for a document chat query."""

    question: str = Field(
        ..., description="Question about the uploaded document.", min_length=3, max_length=500
    )


class DocumentChatResponse(BaseModel):
    """Chat response returned from a document retrieval query."""

    document_id: int = Field(description="ID of the document that was queried.")
    question: str = Field(description="Original question submitted by the user.")
    answer: str = Field(description="LLM-generated answer grounded in the document.")
    sources: list[str] = Field(description="Document chunk texts used as sources for the answer.")

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


@router.post(
    "/documents/{document_id}/chat",
    response_model=DocumentChatResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def chat_document(
    document_id: int,
    request: DocumentChatRequest,
    session: Session = Depends(get_session),
) -> DocumentChatResponse:
    """Answer a natural-language question about an uploaded document."""
    repo = DocumentRepository(session)
    document = repo.get_document(document_id)

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        answer, sources = answer_question(request.question, document_id, repo)
    except ValueError as exc:
        detail = str(exc)
        if "No embedded chunks found" in detail:
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=500, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Document chat failed: {exc}") from exc

    return DocumentChatResponse(
        document_id=document_id,
        question=request.question,
        answer=answer,
        sources=sources,
    )
