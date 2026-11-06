"""密码哈希与 JWT 签发/校验。"""

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_uses_argon2_and_verifies() -> None:
    hashed = hash_password("correct horse battery staple")
    assert hashed.startswith("$argon2")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_verify_password_handles_corrupt_hash_without_raising() -> None:
    assert verify_password("whatever", "not-a-valid-hash") is False


def test_access_and_refresh_tokens_have_distinct_types() -> None:
    access = decode_token(create_access_token(7))
    refresh_token, jti = create_refresh_token(7)
    refresh = decode_token(refresh_token)

    assert access["type"] == "access"
    assert refresh["type"] == "refresh"
    assert access["sub"] == "7"
    assert refresh["jti"] == jti


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(1)
    with pytest.raises(Exception):
        decode_token(token + "x")