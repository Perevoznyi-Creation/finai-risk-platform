from unittest.mock import MagicMock, patch

import pytest

from app.repositories.session import _sqlite_connect_args, get_engine, get_session, init_db


@pytest.fixture(autouse=True)
def clear_engine_cache():
    get_engine.cache_clear()
    yield
    get_engine.cache_clear()


def test_sqlite_connect_args_returns_false_for_sqlite() -> None:
    result = _sqlite_connect_args("sqlite:///test.db")
    assert result == {"check_same_thread": False}


def test_sqlite_connect_args_returns_empty_for_postgres() -> None:
    result = _sqlite_connect_args("postgresql://user:pass@localhost/db")
    assert result == {}


def test_sqlite_connect_args_returns_empty_for_mysql() -> None:
    result = _sqlite_connect_args("mysql://user:pass@localhost/db")
    assert result == {}


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite:///test.db",
        "sqlite:///:memory:",
        "postgresql://localhost/test",
    ],
)
def test_sqlite_connect_args_various_urls(database_url: str) -> None:
    result = _sqlite_connect_args(database_url)
    if database_url.startswith("sqlite"):
        assert result == {"check_same_thread": False}
    else:
        assert result == {}


@patch("app.repositories.session.get_settings")
@patch("app.repositories.session.create_engine")
def test_get_engine_creates_engine_with_settings(
    mock_create_engine: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    mock_settings = MagicMock()
    mock_settings.database_url = "postgresql://localhost/test"
    mock_get_settings.return_value = mock_settings

    engine = get_engine()

    assert engine == mock_create_engine.return_value
    mock_create_engine.assert_called_once_with(
        "postgresql://localhost/test",
        echo=False,
        pool_pre_ping=True,
        connect_args={},
    )


@patch("app.repositories.session.get_settings")
@patch("app.repositories.session.create_engine")
def test_get_engine_with_sqlite_passes_connect_args(
    mock_create_engine: MagicMock,
    mock_get_settings: MagicMock,
) -> None:
    mock_settings = MagicMock()
    mock_settings.database_url = "sqlite:///test.db"
    mock_get_settings.return_value = mock_settings

    engine = get_engine()

    assert engine == mock_create_engine.return_value
    mock_create_engine.assert_called_once_with(
        "sqlite:///test.db",
        echo=False,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )


@patch("app.repositories.session.get_engine")
def test_get_session_yields_session(mock_get_engine: MagicMock) -> None:
    mock_session = MagicMock()
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    with patch("app.repositories.session.Session") as mock_session_class:
        mock_session_class.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_class.return_value.__exit__ = MagicMock(return_value=False)

        session_generator = get_session()
        result = next(session_generator)

    assert result == mock_session


@patch("app.repositories.session.get_engine")
def test_init_db_creates_tables(mock_get_engine: MagicMock) -> None:
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    with patch("app.repositories.session.SQLModel") as mock_sqlmodel:
        init_db()

    mock_sqlmodel.metadata.create_all.assert_called_once_with(mock_engine)