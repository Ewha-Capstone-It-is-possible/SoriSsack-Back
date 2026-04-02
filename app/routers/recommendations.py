from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyBasicInformation, BabyCard
from app.schemas import RecommendationRequest, SuccessResponse
from app.services.ai_client import fetch_recommendations


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=SuccessResponse)
async def recommend_words(payload: RecommendationRequest, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, payload.baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    baby_card = db.get(BabyCard, payload.selected_baby_card_id)
    if baby_card is None or baby_card.baby_id != payload.baby_id:
        raise HTTPException(status_code=404, detail="선택한 아동 카드를 찾을 수 없습니다.")

    result = await fetch_recommendations(payload)
    return SuccessResponse(
        data=result,
        message="추천 단어를 조회했습니다.",
    )
