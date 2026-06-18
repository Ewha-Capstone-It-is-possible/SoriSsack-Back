"""
app/routers/auth.py
-------------------
인증: 회원가입 / 아이디 중복확인 / 로그인 / 내 정보 / 카카오 로그인(준비중).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent
from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_db
from app.models import Parent
from app.schemas import (
    CheckIdData,
    KakaoLoginRequest,
    LoginRequest,
    ParentOut,
    SignupRequest,
    SuccessResponse,
    TokenData,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(parent: Parent) -> TokenData:
    return TokenData(
        access_token=create_access_token(parent.parent_id),
        token_type="bearer",
        parent=ParentOut.model_validate(parent),
    )


@router.get(
    "/check-id",
    response_model=SuccessResponse[CheckIdData],
    summary="아이디 중복 확인",
)
def check_id(user_id: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    exists = db.query(Parent).filter(Parent.user_id == user_id).first() is not None
    return SuccessResponse(
        data=CheckIdData(user_id=user_id, available=not exists),
        message="사용 가능한 아이디입니다." if not exists else "이미 사용 중인 아이디입니다.",
    )


@router.post(
    "/signup",
    response_model=SuccessResponse[TokenData],
    summary="회원가입",
    description="부모 계정을 생성하고 바로 로그인 토큰을 발급한다.",
    responses={409: {"description": "이미 사용 중인 아이디입니다."}},
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if db.query(Parent).filter(Parent.user_id == payload.user_id).first():
        raise HTTPException(status_code=409, detail="이미 사용 중인 아이디입니다.")

    parent = Parent(
        user_id=payload.user_id,
        password_hash=hash_password(payload.password),
        parent_name=payload.parent_name,
        email=payload.email,
        phone_number=payload.phone_number,
        provider="local",
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)

    return SuccessResponse(data=_issue_token(parent), message="회원가입이 완료되었습니다.")


@router.post(
    "/login",
    response_model=SuccessResponse[TokenData],
    summary="로그인",
    description="아이디/비밀번호로 로그인하고 JWT 액세스 토큰을 발급한다.",
    responses={401: {"description": "아이디 또는 비밀번호가 올바르지 않습니다."}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    parent = db.query(Parent).filter(Parent.user_id == payload.user_id).first()
    if parent is None or not parent.password_hash or not verify_password(
        payload.password, parent.password_hash
    ):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    return SuccessResponse(data=_issue_token(parent), message="로그인되었습니다.")


@router.get(
    "/me",
    response_model=SuccessResponse[ParentOut],
    summary="내 정보 (로그인 필요)",
)
def me(parent: Parent = Depends(get_current_parent)):
    return SuccessResponse(data=ParentOut.model_validate(parent), message="내 정보입니다.")


@router.post(
    "/kakao",
    response_model=SuccessResponse[TokenData],
    summary="카카오 로그인 (준비중)",
    description="프론트가 카카오 SDK 로 받은 access token 으로 로그인. "
                "현재는 KAKAO_REST_API_KEY 미설정으로 501 을 반환한다(추후 활성화).",
    responses={501: {"description": "카카오 로그인은 아직 준비 중입니다."}},
)
def kakao_login(payload: KakaoLoginRequest, db: Session = Depends(get_db)):
    # TODO: 카카오 키 발급 후 활성화
    #   1) https://kapi.kakao.com/v2/user/me 에 kakao_access_token 으로 사용자 조회
    #   2) kakao_id 로 Parent 조회 → 없으면 생성(provider="kakao")
    #   3) _issue_token(parent) 반환
    raise HTTPException(status_code=501, detail="카카오 로그인은 아직 준비 중입니다.")
