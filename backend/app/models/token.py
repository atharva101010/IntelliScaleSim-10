from sqlalchemy import Integer, String, DateTime, Enum as SAEnum, ForeignKey, func, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum
from datetime import datetime


class TokenType(str, enum.Enum):
    verify = "verify"
    reset = "reset"


class UserToken(Base):
    __tablename__ = "user_tokens"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_user_tokens_token_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[TokenType] = mapped_column(SAEnum(TokenType), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
