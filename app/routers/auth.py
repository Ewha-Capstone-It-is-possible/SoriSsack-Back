import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyAppSettings, BabyBasicInformation, ParentAccount, ParentSession
from app.schemas import (
    AuthSessionData,
    LogoutData,
    LoginRequest,
    ParentAccountOut,
    PinVerifyData,
    PinVerifyRequest,
    RegisterParentRequest,
    SuccessResponse,
)


router = APIRouter(prefix="/auth", tags=["auth"])

TOKEN_EXPIRE_HOURS = 24


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    actual_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        actual_salt.encode("utf-8"),
        100_000,
    ).hex()
    return actual_salt + "$" + digest


def _verify_password(password: str, hashed_value: str) -> bool:
    try:
        salt, digest = hashed_value.split("$", 1)
    except ValueError:
        return False
    candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, salt + "$" + digest)


def _create_session(parent: ParentAccount, db: Session) -> ParentSession:
    token = secrets.token_urlsafe(32)
    session = ParentSession(
        parent_id=parent.parent_id,
        access_token=token,
        expires_at=datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _session_data(session: ParentSession) -> AuthSessionData:
    return AuthSessionData(
        access_token=session.access_token,
        token_type="bearer",
        expires_at=session.expires_at,
        parent=ParentAccountOut.model_validate(session.parent),
    )


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization 헤더가 필요합니다.")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="Bearer 토큰 형식이 아닙니다.")
    token = authorization[len(prefix):].strip()
    if not token:
        raise HTTPException(status_code=401, detail="액세스 토큰이 비어 있습니다.")
    return token


def get_current_session(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> ParentSession:
    token = _extract_bearer_token(authorization)
    session = (
        db.query(ParentSession)
        .join(ParentAccount, ParentAccount.parent_id == ParentSession.parent_id)
        .filter(
            ParentSession.access_token == token,
            ParentSession.revoked_at.is_(None),
            ParentSession.expires_at > datetime.utcnow(),
            ParentAccount.is_active.is_(True),
        )
        .first()
    )
    if session is None:
        raise HTTPException(status_code=401, detail="유효한 로그인 세션이 아닙니다.")
    return session


@router.post(
    "/register",
    response_model=SuccessResponse[AuthSessionData],
    summary="보호자 회원가입",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}, 409: {"description": "이미 존재하는 이메일입니다."}},
)
def register_parent(payload: RegisterParentRequest, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, payload.baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    existing = db.query(ParentAccount).filter(ParentAccount.email == payload.email.strip().lower()).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="이미 존재하는 이메일입니다.")

    parent = ParentAccount(
        baby_id=payload.baby_id,
        parent_name=payload.parent_name.strip(),
        email=payload.email.strip().lower(),
        password_hash=_hash_password(payload.password),
        is_active=True,
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)

    session = _create_session(parent, db)
    return SuccessResponse(
        data=_session_data(session),
        message="보호자 회원가입 및 로그인을 완료했습니다.",
    )


@router.post(
    "/login",
    response_model=SuccessResponse[AuthSessionData],
    summary="보호자 로그인",
    responses={401: {"description": "이메일 또는 비밀번호가 올바르지 않습니다."}},
)
def login_parent(payload: LoginRequest, db: Session = Depends(get_db)):
    parent = (
        db.query(ParentAccount)
        .filter(ParentAccount.email == payload.email.strip().lower(), ParentAccount.is_active.is_(True))
        .first()
    )
    if parent is None or not _verify_password(payload.password, parent.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    session = _create_session(parent, db)
    return SuccessResponse(
        data=_session_data(session),
        message="로그인에 성공했습니다.",
    )


@router.get(
    "/me",
    response_model=SuccessResponse[ParentAccountOut],
    summary="현재 로그인한 보호자 정보 조회",
    responses={401: {"description": "유효한 로그인 세션이 아닙니다."}},
)
def get_me(session: ParentSession = Depends(get_current_session)):
    return SuccessResponse(
        data=ParentAccountOut.model_validate(session.parent),
        message="현재 로그인한 보호자 정보를 조회했습니다.",
    )


@router.post(
    "/logout",
    response_model=SuccessResponse[LogoutData],
    summary="로그아웃",
    responses={401: {"description": "유효한 로그인 세션이 아닙니다."}},
)
def logout_parent(
    session: ParentSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    session.revoked_at = datetime.utcnow()
    db.commit()
    return SuccessResponse(
        data=LogoutData(logged_out=True),
        message="로그아웃했습니다.",
    )


@router.post(
    "/verify-pin",
    response_model=SuccessResponse[PinVerifyData],
    summary="부모 모드 PIN 확인",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}, 401: {"description": "PIN 이 올바르지 않습니다."}},
)
def verify_parent_pin(payload: PinVerifyRequest, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, payload.baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    app_settings = db.get(BabyAppSettings, payload.baby_id)
    if app_settings is None or not app_settings.parent_pin:
        raise HTTPException(status_code=401, detail="설정된 부모 PIN 이 없습니다.")

    if app_settings.parent_pin != payload.pin:
        raise HTTPException(status_code=401, detail="PIN 이 올바르지 않습니다.")

    return SuccessResponse(
        data=PinVerifyData(baby_id=payload.baby_id, verified=True),
        message="부모 PIN 확인에 성공했습니다.",
    )
