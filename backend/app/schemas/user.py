from pydantic import BaseModel, EmailStr, field_serializer
from typing import Literal, Any


class UserOut(BaseModel):
	id: int
	name: str
	email: EmailStr
	role: Literal["student", "teacher", "admin"]
	is_verified: bool

	class Config:
		from_attributes = True

	@field_serializer("role")
	def serialize_role(self, v: Any):
		try:
			return v.value
		except AttributeError:
			return v

