"""Document service — text extraction, chunking, and embedding storage."""

import io

from pypdf import PdfReader
from sqlmodel import Session

from app.repositories.document_repo import DocumentRepository
from app.repositories.models import DocumentChunk
from app.services.embeddings import embed_text

_CHUNK_SIZE = 500   # characters per chunk
_CHUNK_OVERLAP = 50  # characters of overlap between consecutive chunks


def _extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract plain text from a PDF or text file.

    Args:
        filename: Original filename used to detect file type.
        file_bytes: Raw file content.

    Returns:
        Extracted text string.

    Raises:
        ValueError: If the file type is unsupported or text extraction fails.
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            raise ValueError("Could not extract text from PDF — it may be image-based.")
        return text
    if lower.endswith(".txt") or lower.endswith(".md"):
        return file_bytes.decode("utf-8", errors="replace").strip()
    raise ValueError(
        f"Unsupported file type '{filename}'. Upload a .pdf, .txt, or .md file."
    )


def _split_into_chunks(text: str) -> list[str]:
    """Split text into overlapping fixed-size character chunks.

    Args:
        text: The full document text.

    Returns:
        List of text chunk strings.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append(text[start:end])
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


def ingest_document(
    filename: str, file_bytes: bytes, session: Session
) -> tuple[int, int]:
    """Extract, chunk, embed, and persist a document.

    Args:
        filename: Original uploaded filename.
        file_bytes: Raw file content.
        session: Active database session.

    Returns:
        Tuple of ``(document_id, chunk_count)``.

    Raises:
        ValueError: On unsupported file type or empty PDF.
    """
    text = _extract_text(filename, file_bytes)
    raw_chunks = _split_into_chunks(text)

    repo = DocumentRepository(session)
    doc = repo.save_document(filename=filename, content_text=text)

    chunks: list[DocumentChunk] = []
    for idx, chunk_text in enumerate(raw_chunks):
        embedding = embed_text(chunk_text)
        chunks.append(
            DocumentChunk(
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=chunk_text,
                embedding=embedding,
            )
        )

    repo.save_chunks(chunks)
    return doc.id, len(chunks)
