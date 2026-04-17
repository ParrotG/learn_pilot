from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import ExternalConfigurationError, UnauthorizedError

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class TokenPayload(BaseModel):
    sub: str
    exp: int


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str, settings: Settings) -> str:
    expire_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": int(expire_at.timestamp())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired access token.") from exc
    return TokenPayload.model_validate(payload)


def _get_fernet(settings: Settings) -> Fernet:
    try:
        return Fernet(settings.app_encryption_key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise ExternalConfigurationError(
            "APP_ENCRYPTION_KEY is missing or invalid. Generate a Fernet key before using credential storage."
        ) from exc


def encrypt_value(value: str, settings: Settings) -> str:
    return _get_fernet(settings).encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: str, settings: Settings) -> str:
    try:
        return _get_fernet(settings).decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ExternalConfigurationError(
            "Stored encrypted data could not be decrypted with the current APP_ENCRYPTION_KEY."
        ) from exc


def create_signed_state(*, user_id: str, settings: Settings) -> str:
    expire_at = datetime.now(UTC) + timedelta(minutes=10)
    payload = {"sub": user_id, "exp": int(expire_at.timestamp())}
    return jwt.encode(payload, settings.google_oauth_state_secret, algorithm="HS256")


def verify_signed_state(state: str, settings: Settings) -> str:
    try:
        payload = jwt.decode(state, settings.google_oauth_state_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise UnauthorizedError("Invalid Google OAuth state.") from exc
    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedError("Invalid Google OAuth state.")
    return str(subject)
