from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Literal
import re


RoleLiteral = Literal["student", "teacher", "admin"]


class RegisterRequest(BaseModel):
	name: str = Field(min_length=1, max_length=100)
	email: EmailStr
	password: str = Field(min_length=8, max_length=128)
	role: RoleLiteral = "student"

	@field_validator("password")
	@classmethod
	def strong_password(cls, v: str) -> str:
		# Require at least one letter and one special character
		if not re.search(r"[A-Za-z]", v):
			raise ValueError("Password must contain at least one letter")
		if not re.search(r"[^A-Za-z0-9]", v):
			raise ValueError("Password must contain at least one special character")
		return v


class LoginRequest(BaseModel):
	email: EmailStr
	password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
	access_token: str
	token_type: str = "bearer"


class RequestEmailVerification(BaseModel):
	email: EmailStr


class ConfirmEmailVerification(BaseModel):
	token: str = Field(min_length=10)


class ForgotPasswordRequest(BaseModel):
	email: EmailStr


class ResetPasswordRequest(BaseModel):
	token: str = Field(min_length=10)
	new_password: str = Field(min_length=8, max_length=128)

	@field_validator("new_password")
	@classmethod
	def strong_password(cls, v: str) -> str:
		if not re.search(r"[A-Za-z]", v):
			raise ValueError("Password must contain at least one letter")
		if not re.search(r"[^A-Za-z0-9]", v):
			raise ValueError("Password must contain at least one special character")
		return v

