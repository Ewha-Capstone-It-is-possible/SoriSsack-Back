from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_owned_baby
from app.db import get_db
from app.models import (
    BabyCard,
    BabyCardCategoryMap,
    BabyCategory,
    CardCategoryMapMaster,
    CardMaster,
    CategoryMaster,
    Parent,
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
    summary="부모 단어추가용 관련 단어 추천 (로그인 필요)",
)
async def suggest_words(
    payload: SuggestWordsRequest,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """
    부모 '단어 추가'용 관련 단어 추천. 입력 텍스트와 관련된, **DB 에 아직 없는** 새 단어를
    AI(GPT)로 제안한다. 이미 카드로 있는 단어는 제외한다.
    """
    if payload.baby_id is not None:
        get_owned_baby(payload.baby_id, parent, db)

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
    summary="아동 카드 목록 조회 (로그인 필요)",
    responses={
        403: {"description": "이 아동에 접근할 권한이 없습니다."},
        404: {"description": "아동 정보를 찾을 수 없습니다."},
    },
)
def get_cards(
    baby_id: int,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    get_owned_baby(baby_id, parent, db)

    baby_cards = (
        db.query(BabyCard)
        .filter(BabyCard.baby_id == baby_id, BabyCard.is_active.is_(True), BabyCard.status != "off")
        .all()
    )

    overridden_card_ids = {c.card_id for c in baby_cards if c.card_id is not None}
    master_q = db.query(CardMaster).filter(CardMaster.is_active.is_(True))
    if overridden_card_ids:
        master_q = master_q.filter(~CardMaster.card_id.in_(overridden_card_ids))
    master_cards = master_q.all()

    # baby_category 조회 (개인 카테고리)
    baby_category_rows = (
        db.query(BabyCategory)
        .filter(BabyCategory.baby_id == baby_id, BabyCategory.is_enabled.is_(True))
        .all()
    )
    bcat_by_id = {r.baby_category_id: r for r in baby_category_rows}
    bcat_by_master_id = {r.category_id: r for r in baby_category_rows if r.category_id is not None}

    # baby_card_id → CardCategoryOut (개인 카드 카테고리 매핑)
    bc_cat_map = (
        db.query(BabyCardCategoryMap)
        .filter(BabyCardCategoryMap.baby_id == baby_id)
        .all()
    )
    bc_cat_by_bcid: dict[int, CardCategoryOut] = {}
    for row in bc_cat_map:
        bcat = bcat_by_id.get(row.baby_category_id)
        if bcat is None:
            continue
        bc_cat_by_bcid.setdefault(
            row.baby_card_id,
            CardCategoryOut(
                baby_category_id=bcat.baby_category_id,
                category_id=bcat.category_id,
                name=bcat.name,
                icon_url=bcat.icon_url,
            ),
        )

    # card_id → CardCategoryOut (마스터 카드 카테고리 매핑)
    master_cat_rows = (
        db.query(
            CardCategoryMapMaster.card_id,
            CardCategoryMapMaster.is_primary,
            CategoryMaster.category_id,
            CategoryMaster.name,
            CategoryMaster.icon_url,
        )
        .join(CategoryMaster, CategoryMaster.category_id == CardCategoryMapMaster.category_id)
        .filter(CardCategoryMapMaster.is_active.is_(True))
        .order_by(CardCategoryMapMaster.is_primary.desc(), CategoryMaster.name)
        .all()
    )
    master_cat_by_cid: dict[int, CardCategoryOut] = {}
    for row in master_cat_rows:
        if row.card_id in master_cat_by_cid:
            continue
        bcat = bcat_by_master_id.get(row.category_id)
        master_cat_by_cid[row.card_id] = CardCategoryOut(
            baby_category_id=bcat.baby_category_id if bcat else None,
            category_id=row.category_id,
            name=bcat.name if bcat else row.name,
            icon_url=(bcat.icon_url if bcat else None) or row.icon_url,
        )

    result: list[CardOut] = []

    for card in baby_cards:
        category = bc_cat_by_bcid.get(card.baby_card_id)
        if category is None and card.card_id is not None:
            category = master_cat_by_cid.get(card.card_id)
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

    for cm in master_cards:
        result.append(
            CardOut(
                baby_card_id=None,
                card_id=cm.card_id,
                text=cm.base_text,
                part_of_speech=cm.part_of_speech,
                image_url=cm.default_image_url,
                is_favorite=False,
                source="system_default",
                status="default",
                usage_count=0,
                category=master_cat_by_cid.get(cm.card_id),
            )
        )

    return SuccessResponse(data=result, message="카드 목록을 조회했습니다.")
