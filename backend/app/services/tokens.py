import secrets
import hashlib
from datetime import datetime, timedelta, timezone


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def expiry_in(minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)
