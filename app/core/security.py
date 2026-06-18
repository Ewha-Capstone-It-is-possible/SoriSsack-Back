"""
app/core/security.py
--------------------
비밀번호 해시(bcrypt) + JWT 토큰 발급/검증.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


# -------------------------------------------------------
# 비밀번호 해시
# -------------------------------------------------------
def hash_password(plain: str) -> str:
    """평문 비밀번호 → bcrypt 해시 문자열."""
    # bcrypt 는 72바이트 초과분을 무시하므로 안전하게 잘라 인코딩
    pw = plain.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """평문이 해시와 일치하는지 검증."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# -------------------------------------------------------
# JWT
# -------------------------------------------------------
def create_access_token(parent_id: int) -> str:
    """parent_id 를 sub 로 담은 액세스 토큰 발급."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(parent_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """토큰 검증 후 payload 반환. 만료/위조면 jwt 예외 발생."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
