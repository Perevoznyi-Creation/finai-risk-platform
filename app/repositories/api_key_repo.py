"""ApiKey repository — encapsulates all database queries for API key records."""

from sqlmodel import Session, select

from app.repositories.models import ApiKey


class ApiKeyRepository:
    """Manages persistence and lookup of API key records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> list[ApiKey]:
        """Return all stored API key records."""
        return list(self._session.exec(select(ApiKey)).all())

    def get_by_name(self, name: str) -> ApiKey | None:
        """Return the API key record with the given name, or None."""
        return self._session.exec(
            select(ApiKey).where(ApiKey.name == name)
        ).first()

    def save(self, key: ApiKey) -> ApiKey:
        """Persist a new or updated API key record and return the refreshed row."""
        self._session.add(key)
        self._session.commit()
        self._session.refresh(key)
        return key
