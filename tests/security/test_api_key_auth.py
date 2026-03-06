from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.db.models import ApiKey
from app.security import api_key as api_key_security


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def exec(self, _):
        return _FakeResult(self._rows)


def test_hash_api_key_is_deterministic() -> None:
    salt = "test-salt"
    key = "my-secret-key"

    first = api_key_security.hash_api_key(key, salt)
    second = api_key_security.hash_api_key(key, salt)

    assert first == second
    assert len(first) == 64


def test_verify_api_key_hash_true_and_false() -> None:
    salt = "test-salt"
    raw_key = "my-secret-key"
    stored_hash = api_key_security.hash_api_key(raw_key, salt)

    assert api_key_security.verify_api_key_hash(raw_key, stored_hash, salt)
    assert not api_key_security.verify_api_key_hash("wrong-key", stored_hash, salt)


def test_build_api_key_record_hashes_and_sets_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_key_security,
        "get_settings",
        lambda: SimpleNamespace(api_key_salt="salt-123"),
    )

    record = api_key_security.build_api_key_record("default", "raw-key")

    assert record.name == "default"
    assert record.is_active is True
    assert record.key_hash == api_key_security.hash_api_key("raw-key", "salt-123")


def test_require_api_key_missing_header_raises_401() -> None:
    with pytest.raises(HTTPException) as exc:
        api_key_security.require_api_key(api_key=None, session=_FakeSession([]))

    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing API key."


def test_require_api_key_invalid_hash_raises_401(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_key_security,
        "get_settings",
        lambda: SimpleNamespace(api_key_salt="salt-123"),
    )
    key_row = ApiKey(name="active", key_hash="another-hash", is_active=True)

    with pytest.raises(HTTPException) as exc:
        api_key_security.require_api_key(
            api_key="raw-key",
            session=_FakeSession([key_row]),
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid API key."


def test_require_api_key_inactive_match_raises_403(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_key_security,
        "get_settings",
        lambda: SimpleNamespace(api_key_salt="salt-123"),
    )
    inactive_hash = api_key_security.hash_api_key("raw-key", "salt-123")
    key_row = ApiKey(name="inactive", key_hash=inactive_hash, is_active=False)

    with pytest.raises(HTTPException) as exc:
        api_key_security.require_api_key(
            api_key="raw-key",
            session=_FakeSession([key_row]),
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "API key is inactive."


def test_require_api_key_active_match_returns_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_key_security,
        "get_settings",
        lambda: SimpleNamespace(api_key_salt="salt-123"),
    )
    active_hash = api_key_security.hash_api_key("raw-key", "salt-123")
    key_row = ApiKey(name="active", key_hash=active_hash, is_active=True)

    result = api_key_security.require_api_key(
        api_key="raw-key",
        session=_FakeSession([key_row]),
    )

    assert result.name == "active"
    assert result.is_active is True
