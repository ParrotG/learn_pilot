from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse, UserUpdateRequest


class AuthService:
    async def register_user(self, session: AsyncSession, payload: UserRegisterRequest) -> User:
        existing = await session.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("An account with this email already exists.")

        user = User(
            email=payload.email.lower(),
            password_hash=get_password_hash(payload.password),
            full_name=payload.full_name,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def authenticate_user(self, session: AsyncSession, payload: UserLoginRequest) -> User:
        result = await session.execute(select(User).where(User.email == payload.email.lower()))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")
        return user

    async def update_profile(
        self, session: AsyncSession, user: User, payload: UserUpdateRequest
    ) -> User:
        user.full_name = payload.full_name
        await session.commit()
        await session.refresh(user)
        return user

    def create_token_response(self, *, user: User, settings: Settings) -> TokenResponse:
        access_token = create_access_token(subject=user.id, settings=settings)
        return TokenResponse(access_token=access_token, user=UserResponse.model_validate(user))

