from __future__ import annotations

from cryptography.fernet import Fernet

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    decrypt_value,
    encrypt_value,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_token_round_trip() -> None:
    password = "VerySecure123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)

    settings = Settings(
        jwt_secret_key="secret",
        google_oauth_state_secret="state-secret",
        app_encryption_key=Fernet.generate_key().decode("utf-8"),
    )
    token = create_access_token(subject="user-123", settings=settings)
    payload = decode_access_token(token, settings)
    assert payload.sub == "user-123"


def test_encrypt_and_decrypt_round_trip() -> None:
    settings = Settings(
        jwt_secret_key="secret",
        google_oauth_state_secret="state-secret",
        app_encryption_key=Fernet.generate_key().decode("utf-8"),
    )
    encrypted = encrypt_value("api-key-value", settings)
    decrypted = decrypt_value(encrypted, settings)
    assert decrypted == "api-key-value"

