from fastapi import APIRouter

from app.schemas import SuccessResponse


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=SuccessResponse)
def health_check():
    return SuccessResponse(
        data={"status": "ok"},
        message="서버가 정상 동작 중입니다.",
    )
