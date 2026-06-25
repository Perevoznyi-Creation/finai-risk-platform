"""Document repository — persistence for uploaded documents and their chunks."""

from sqlalchemy import text
from sqlmodel import Session, select

from app.repositories.models import Document, DocumentChunk


class DocumentRepository:
    """Manages persistence and lookup of documents and their text chunks."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save_document(self, filename: str, content_text: str) -> Document:
        """Persist a new document and return the saved row with its ID."""
        doc = Document(filename=filename, content_text=content_text)
        self._session.add(doc)
        self._session.commit()
        self._session.refresh(doc)
        return doc

    def get_document(self, document_id: int) -> Document | None:
        """Return a document by ID, or None if not found."""
        return self._session.get(Document, document_id)

    def save_chunks(self, chunks: list[DocumentChunk]) -> None:
        """Bulk-insert a list of document chunks."""
        for chunk in chunks:
            self._session.add(chunk)
        self._session.commit()

    def search_chunks_by_embedding(
        self, embedding: list[float], document_id: int | None = None, limit: int = 5
    ) -> list[DocumentChunk]:
        """Return the closest document chunks to the given embedding vector.

        Args:
            embedding: Query vector (384 dimensions).
            document_id: If provided, restrict search to this document only.
            limit: Maximum number of results.

        Returns:
            List of DocumentChunk rows ordered by cosine similarity (closest first).
        """
        vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.embedding.is_not(None))  # type: ignore[union-attr]
            .order_by(text(f"embedding <=> '{vector_literal}'::vector"))
            .limit(limit)
        )
        if document_id is not None:
            stmt = stmt.where(DocumentChunk.document_id == document_id)
        return list(self._session.exec(stmt).all())
