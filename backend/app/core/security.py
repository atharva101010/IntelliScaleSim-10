from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
	return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
	return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_minutes: Optional[int] = None) -> str:
	to_encode = data.copy()
	expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
	expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
	return encoded_jwt
