from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyBasicInformation, BabyCard, CardMaster
from app.schemas import CardOut, SuccessResponse


router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/{baby_id}", response_model=SuccessResponse)
def get_cards(baby_id: int, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    baby_cards = (
        db.query(BabyCard)
        .filter(BabyCard.baby_id == baby_id, BabyCard.is_active.is_(True), BabyCard.status != "off")
        .all()
    )

    overridden_card_ids = {card.card_id for card in baby_cards if card.card_id is not None}
    master_cards = (
        db.query(CardMaster)
        .filter(CardMaster.is_active.is_(True))
        .filter(~CardMaster.card_id.in_(overridden_card_ids) if overridden_card_ids else True)
        .all()
    )

    result: list[CardOut] = []

    for card in baby_cards:
        result.append(
            CardOut(
                baby_card_id=card.baby_card_id,
                card_id=card.card_id,
                text=card.text or (card.card_master.base_text if card.card_master else ""),
                part_of_speech=card.part_of_speech or (card.card_master.part_of_speech if card.card_master else None),
                image_url=card.custom_image_url or (card.card_master.default_image_url if card.card_master else None),
                is_favorite=card.is_favorite,
                source=card.source,
                status=card.status,
                usage_count=card.usage_count,
            )
        )

    for card in master_cards:
        result.append(
            CardOut(
                baby_card_id=None,
                card_id=card.card_id,
                text=card.base_text,
                part_of_speech=card.part_of_speech,
                image_url=card.default_image_url,
                is_favorite=False,
                source="system_default",
                status="default",
                usage_count=0,
            )
        )

    return SuccessResponse(
        data=result,
        message="카드 목록을 조회했습니다.",
    )
