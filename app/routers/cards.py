from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    BabyBasicInformation,
    BabyCard,
    BabyCardCategoryMap,
    BabyCategory,
    CardCategoryMapMaster,
    CardMaster,
)
from app.schemas import (
    CardCategoryOut,
    CardOut,
    SuccessResponse,
    SuggestionsData,
    SuggestWordsRequest,
)
from app.services.ai_client import fetch_related_words


router = APIRouter(prefix="/cards", tags=["cards"])


@router.post(
    "/suggest",
    response_model=SuccessResponse[SuggestionsData],
    summary="부모 단어추가용 관련 단어 추천",
)
async def suggest_words(payload: SuggestWordsRequest, db: Session = Depends(get_db)):
    """
    부모 '단어 추가'용 관련 단어 추천. 입력 텍스트와 관련된, **DB 에 아직 없는** 새 단어를
    AI(GPT)로 제안한다. 이미 카드로 있는 단어는 제외한다.
    """
    existing: set[str] = set()
    for (text,) in db.query(CardMaster.base_text).all():
        if text:
            existing.add(text.strip())
    baby_card_query = db.query(BabyCard.text).filter(BabyCard.text.isnot(None))
    if payload.baby_id is not None:
        baby_card_query = baby_card_query.filter(BabyCard.baby_id == payload.baby_id)
    for (text,) in baby_card_query.all():
        if text:
            existing.add(text.strip())

    items = await fetch_related_words(
        text=payload.text, count=payload.count, exclude=sorted(existing)
    )
    # 안전 필터: DB 에 없는 새 단어만 남김
    suggestions = [
        {"text": w.get("text"), "pos": w.get("pos")}
        for w in items
        if w.get("text") and w["text"].strip() not in existing
    ]

    return SuccessResponse(
        data={"text": payload.text, "suggestions": suggestions},
        message="관련 단어를 추천했습니다.",
    )


@router.get(
    "/{baby_id}",
    response_model=SuccessResponse[list[CardOut]],
    summary="아동 카드 목록 조회",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
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

    baby_category_rows = (
        db.query(BabyCategory)
        .filter(BabyCategory.baby_id == baby_id, BabyCategory.is_enabled.is_(True))
        .all()
    )
    baby_category_by_id = {row.baby_category_id: row for row in baby_category_rows}
    baby_category_by_master_id = {
        row.category_id: row for row in baby_category_rows if row.category_id is not None
    }

    baby_card_category_maps = (
        db.query(BabyCardCategoryMap)
        .filter(BabyCardCategoryMap.baby_id == baby_id)
        .all()
    )
    baby_card_categories_by_card_id: dict[int, list[CardCategoryOut]] = {}
    for category_map in baby_card_category_maps:
        baby_category = baby_category_by_id.get(category_map.baby_category_id)
        if baby_category is None:
            continue
        baby_card_categories_by_card_id.setdefault(category_map.baby_card_id, []).append(
            CardCategoryOut(
                baby_category_id=baby_category.baby_category_id,
                category_id=baby_category.category_id,
                name=baby_category.name,
                icon_url=baby_category.icon_url,
            )
        )

    master_card_category_maps = (
        db.query(CardCategoryMapMaster)
        .filter(CardCategoryMapMaster.is_active.is_(True))
        .all()
    )
    master_card_categories_by_card_id: dict[int, list[tuple[bool, CardCategoryOut]]] = {}
    for category_map in master_card_category_maps:
        baby_category = baby_category_by_master_id.get(category_map.category_id)
        if baby_category is not None:
            category = CardCategoryOut(
                baby_category_id=baby_category.baby_category_id,
                category_id=baby_category.category_id,
                name=baby_category.name,
                icon_url=baby_category.icon_url,
            )
        elif category_map.category_master is not None:
            category = CardCategoryOut(
                baby_category_id=None,
                category_id=category_map.category_master.category_id,
                name=category_map.category_master.name,
                icon_url=category_map.category_master.icon_url,
            )
        else:
            continue

        master_card_categories_by_card_id.setdefault(category_map.card_id, []).append((category_map.is_primary, category))

    for card in baby_cards:
        category = next(iter(baby_card_categories_by_card_id.get(card.baby_card_id, [])), None)
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
                category=category,
            )
        )

    for card in master_cards:
        category_candidates = [category for _, category in sorted(
            master_card_categories_by_card_id.get(card.card_id, []),
            key=lambda item: (not item[0], item[1].name),
        )]
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
                category=category_candidates[0] if category_candidates else None,
            )
        )

    return SuccessResponse(
        data=result,
        message="카드 목록을 조회했습니다.",
    )
