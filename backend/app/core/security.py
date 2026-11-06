"""密码哈希（pwdlib）与 JWT（Access + Refresh 双 Token）签发/校验。

- 密码哈希统一使用 pwdlib（passlib 上游 2020 年后停止维护，新项目不引入）。
- 业务代码只调用 hash_password / verify_password，不直接 import pwdlib。
- JWT 含 type(access/refresh) 与 jti 声明；refresh 的 jti 用于 Redis 白名单
  （core/redis_client.py: RedisKeys.AUTH_REFRESH）。
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings
from app.core.exceptions import TokenExpiredError, TokenInvalidError

# 新密码用 Argon2id；同时保留 BcryptHasher 以兼容历史 bcrypt 哈希。
# 顺序有意义：verify 会依次尝试，新 hash 始终由第一个（Argon2）生成。
_password_hasher = PasswordHash((Argon2Hasher(), BcryptHasher()))


# ---------------- 密码哈希 ----------------

def hash_password(password: str) -> str:
    """生成密码哈希（Argon2id）。"""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希是否匹配；哈希格式损坏时按校验失败处理。"""
    try:
        return _password_hasher.verify(plain_password, hashed_password)
    except Exception:
        return False


# ---------------- JWT ----------------

def _create_token(
    subject: str, token_type: Literal["access", "refresh"], expires_delta: timedelta
) -> tuple[str, str]:
    """签发 JWT，返回 (token, jti)。

    jti（JWT ID）唯一标识一个 token，refresh token 的 jti 会写入
    Redis 白名单，用于登出/吊销。
    """
    jti = uuid4().hex
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": now + expires_delta,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_access_token(subject: str | int) -> str:
    """签发短期 Access Token（默认 30 分钟）。"""
    return _create_token(
        str(subject), "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )[0]


def create_refresh_token(subject: str | int) -> tuple[str, str]:
    """签发长期 Refresh Token，返回 (token, jti)。

    jti 供认证层写入 Redis 白名单 `auth:refresh:{jti}`（TTL = 有效期），
    登出时删除即可吊销。
    """
    return _create_token(
        str(subject), "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str) -> dict[str, Any]:
    """解析并校验 JWT，返回 payload。

    校验失败抛 TokenExpiredError / TokenInvalidError（统一由全局异常处理器兜底）。
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except ExpiredSignatureError as exc:
        raise TokenExpiredError from exc
    except JWTError as exc:
        raise TokenInvalidError from exc

    if payload.get("type") not in ("access", "refresh"):
        raise TokenInvalidError
    # 我们签发的 token 一定带 sub/jti；缺失说明 payload 被裁剪或来源异常
    if not payload.get("sub") or not payload.get("jti"):
        raise TokenInvalidError
    return payload
