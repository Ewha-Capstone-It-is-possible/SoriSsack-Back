from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyBasicInformation, BabyCard, BabyVocabLog, SentenceMaster
from app.routers.settings import _settings_out
from app.schemas import BabyOut, MyPageSummaryData, SuccessResponse


router = APIRouter(prefix="/mypage", tags=["mypage"])


@router.get(
    "/{baby_id}",
    response_model=SuccessResponse[MyPageSummaryData],
    summary="마이페이지 요약 조회",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
def get_mypage_summary(baby_id: int, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    total_cards = (
        db.query(func.count(BabyCard.baby_card_id))
        .filter(BabyCard.baby_id == baby_id, BabyCard.is_active.is_(True), BabyCard.status != "off")
        .scalar()
        or 0
    )
    favorite_cards = (
        db.query(func.count(BabyCard.baby_card_id))
        .filter(BabyCard.baby_id == baby_id, BabyCard.is_active.is_(True), BabyCard.is_favorite.is_(True))
        .scalar()
        or 0
    )
    total_logs = (
        db.query(func.count(BabyVocabLog.log_id))
        .filter(BabyVocabLog.baby_id == baby_id)
        .scalar()
        or 0
    )
    total_sentences = (
        db.query(func.count(SentenceMaster.sentence_id))
        .filter(SentenceMaster.baby_id == baby_id)
        .scalar()
        or 0
    )
    latest_sentence = (
        db.query(SentenceMaster)
        .filter(SentenceMaster.baby_id == baby_id)
        .order_by(SentenceMaster.created_at.desc())
        .first()
    )

    return SuccessResponse(
        data=MyPageSummaryData(
            baby=BabyOut.model_validate(baby),
            settings=_settings_out(baby_id, baby.app_settings),
            total_cards=total_cards,
            favorite_cards=favorite_cards,
            total_logs=total_logs,
            total_sentences=total_sentences,
            latest_sentence=latest_sentence.sentence_text if latest_sentence else None,
        ),
        message="마이페이지 요약 정보를 조회했습니다.",
    )
