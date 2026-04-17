from __future__ import annotations

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    payload = decode_access_token(token, settings)
    result = await session.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("The access token is valid, but the user no longer exists.")
    return user

