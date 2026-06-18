from fastapi import APIRouter

from app.schemas import HealthData, SuccessResponse


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=SuccessResponse[HealthData], summary="헬스 체크")
def health_check():
    return SuccessResponse(
        data={"status": "ok"},
        message="서버가 정상 동작 중입니다.",
    )
