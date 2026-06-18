from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_owned_baby
from app.db import get_db
from app.models import BabyCard, Parent
from app.schemas import RecommendationRequest, RecommendationResult, SuccessResponse
from app.services.ai_client import fetch_recommendations


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "",
    response_model=SuccessResponse[RecommendationResult],
    summary="다음 단어 추천 (로그인 필요)",
    responses={
        403: {"description": "이 아동에 접근할 권한이 없습니다."},
        404: {"description": "아동/카드 정보를 찾을 수 없습니다."},
    },
)
async def recommend_words(
    payload: RecommendationRequest,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    get_owned_baby(payload.baby_id, parent, db)

    if payload.selected_baby_card_id is not None:
        baby_card = db.get(BabyCard, payload.selected_baby_card_id)
        if baby_card is None or baby_card.baby_id != payload.baby_id:
            raise HTTPException(status_code=404, detail="선택한 아동 카드를 찾을 수 없습니다.")

    result = await fetch_recommendations(payload)
    return SuccessResponse(
        data=result,
        message="추천 단어를 조회했습니다.",
    )
