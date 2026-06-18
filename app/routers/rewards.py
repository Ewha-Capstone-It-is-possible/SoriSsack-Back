from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyBasicInformation, BabyCard, BabyVocabLog, SentenceMaster
from app.schemas import BadgeOut, RewardsData, SuccessResponse


router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get(
    "/{baby_id}",
    response_model=SuccessResponse[RewardsData],
    summary="보상 현황 조회",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
def get_rewards(baby_id: int, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

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
    favorite_cards = (
        db.query(func.count(BabyCard.baby_card_id))
        .filter(BabyCard.baby_id == baby_id, BabyCard.is_favorite.is_(True), BabyCard.is_active.is_(True))
        .scalar()
        or 0
    )

    reward_enabled = True if baby.app_settings is None else baby.app_settings.reward_enabled
    points = total_logs * 5 + total_sentences * 10 + favorite_cards * 3
    level = max(1, points // 50 + 1)

    badges = [
        BadgeOut(
            key="first_touch",
            title="첫 선택",
            earned=total_logs >= 1,
            description="첫 카드 선택 로그가 저장되면 획득",
        ),
        BadgeOut(
            key="talker",
            title="말하기 시작",
            earned=total_sentences >= 1,
            description="첫 문장을 생성하면 획득",
        ),
        BadgeOut(
            key="routine_builder",
            title="표현 습관 만들기",
            earned=total_logs >= 20,
            description="카드 사용 로그 20회 이상",
        ),
        BadgeOut(
            key="favorite_master",
            title="취향 찾기",
            earned=favorite_cards >= 3,
            description="즐겨찾기 카드 3개 이상 등록",
        ),
    ]

    return SuccessResponse(
        data=RewardsData(
            baby_id=baby_id,
            reward_enabled=reward_enabled,
            points=points,
            level=level,
            badges=badges,
        ),
        message="보상 현황을 조회했습니다.",
    )
