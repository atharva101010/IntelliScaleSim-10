from sqlalchemy import Column, Integer, String, Enum, DateTime, func, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
import enum
from datetime import datetime


class UserRole(str, enum.Enum):
	student = "student"
	teacher = "teacher"
	admin = "admin"


class User(Base):
	__tablename__ = "users"
	__table_args__ = (
		UniqueConstraint("email", name="uq_users_email"),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	name: Mapped[str] = mapped_column(String(100), nullable=False)
	email: Mapped[str] = mapped_column(String(255), nullable=False)
	password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
	role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.student)
	is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
	
	# Relationships
	load_tests = relationship("LoadTest", back_populates="user")

