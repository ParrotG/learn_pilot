from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampedModel


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)


class UserResponse(TimestampedModel):
    email: EmailStr
    full_name: str | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

