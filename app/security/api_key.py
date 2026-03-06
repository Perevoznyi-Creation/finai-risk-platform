"""API-key authentication utilities and dependency wiring."""

import hashlib
import hmac

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlmodel import Session, select

from app.core.config import get_settings
from app.db.models import ApiKey
from app.db.session import get_session

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(raw_api_key: str, salt: str) -> str:
    """Return a deterministic SHA-256 hash for an API key + salt."""

    material = f"{salt}:{raw_api_key}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def verify_api_key_hash(raw_api_key: str, stored_hash: str, salt: str) -> bool:
    """Validate a raw API key against a stored hash with constant-time compare."""

    computed_hash = hash_api_key(raw_api_key, salt)
    return hmac.compare_digest(computed_hash, stored_hash)


def build_api_key_record(name: str, raw_api_key: str, *, is_active: bool = True) -> ApiKey:
    """Create an ApiKey row object with hashed key value."""

    settings = get_settings()
    return ApiKey(
        name=name,
        key_hash=hash_api_key(raw_api_key, settings.api_key_salt),
        is_active=is_active,
    )


def require_api_key(
    api_key: str | None = Security(api_key_header),
    session: Session = Depends(get_session),
) -> ApiKey:
    """Authenticate request using X-API-Key header against DB-stored key hashes."""

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key.")

    settings = get_settings()
    candidate_hash = hash_api_key(api_key, settings.api_key_salt)
    keys = session.exec(select(ApiKey)).all()

    inactive_match = False

    for key_row in keys:
        if hmac.compare_digest(candidate_hash, key_row.key_hash):
            if not key_row.is_active:
                inactive_match = True
                continue
            return key_row

    if inactive_match:
        raise HTTPException(status_code=403, detail="API key is inactive.")

    raise HTTPException(status_code=401, detail="Invalid API key.")
