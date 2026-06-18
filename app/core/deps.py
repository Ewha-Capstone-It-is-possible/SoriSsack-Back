"""
app/core/deps.py
----------------
인증 의존성: 요청의 Bearer 토큰 → 현재 로그인한 부모(Parent).
그리고 baby 소유권 검증(다른 부모의 아이 접근 차단).
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db import get_db
from app.models import BabyBasicInformation, Parent


# Swagger 에 'Authorize' 버튼(Bearer) 노출
bearer_scheme = HTTPBearer(auto_error=True)

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="인증이 필요합니다.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_parent(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Parent:
    """Bearer 토큰을 검증해 현재 로그인한 부모를 반환. 실패 시 401."""
    try:
        payload = decode_access_token(credentials.credentials)
        parent_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _CREDENTIALS_EXC

    parent = db.get(Parent, parent_id)
    if parent is None:
        raise _CREDENTIALS_EXC
    return parent


def get_owned_baby(
    baby_id: int,
    parent: Parent,
    db: Session,
) -> BabyBasicInformation:
    """baby_id 가 현재 부모의 아이인지 검증 후 반환. 아니면 404/403."""
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")
    if baby.parent_id is not None and baby.parent_id != parent.parent_id:
        raise HTTPException(status_code=403, detail="이 아동에 접근할 권한이 없습니다.")
    return baby
