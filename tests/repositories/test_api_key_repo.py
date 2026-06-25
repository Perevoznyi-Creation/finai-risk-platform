from unittest.mock import MagicMock

import pytest

from app.repositories.api_key_repo import ApiKeyRepository
from app.repositories.models import ApiKey


@pytest.fixture
def mock_session() -> MagicMock:
    session = MagicMock()
    return session


def test_get_all_returns_all_keys(mock_session: MagicMock) -> None:
    repo = ApiKeyRepository(mock_session)
    mock_keys = [ApiKey(name="key1"), ApiKey(name="key2")]
    mock_session.exec.return_value.all.return_value = mock_keys

    result = repo.get_all()

    assert result == mock_keys
    mock_session.exec.assert_called_once()


def test_get_by_name_returns_key(mock_session: MagicMock) -> None:
    repo = ApiKeyRepository(mock_session)
    mock_key = ApiKey(name="test-key")
    mock_session.exec.return_value.first.return_value = mock_key

    result = repo.get_by_name("test-key")

    assert result == mock_key
    mock_session.exec.assert_called_once()


def test_get_by_name_returns_none_when_not_found(mock_session: MagicMock) -> None:
    repo = ApiKeyRepository(mock_session)
    mock_session.exec.return_value.first.return_value = None

    result = repo.get_by_name("nonexistent")

    assert result is None
    mock_session.exec.assert_called_once()


def test_save_persists_and_returns_key(mock_session: MagicMock) -> None:
    repo = ApiKeyRepository(mock_session)
    key = ApiKey(name="new-key")

    result = repo.save(key)

    assert result == key
    mock_session.add.assert_called_once_with(key)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(key)