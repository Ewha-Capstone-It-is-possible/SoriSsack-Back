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
    CategoryMaster,
)
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

    overridden_card_ids = {c.card_id for c in baby_cards if c.card_id is not None}
    master_q = db.query(CardMaster).filter(CardMaster.is_active.is_(True))
    if overridden_card_ids:
        master_q = master_q.filter(~CardMaster.card_id.in_(overridden_card_ids))
    master_cards = master_q.all()

    # baby_card_id -> (baby_category_id, name)
    bc_cat_rows = (
        db.query(
            BabyCardCategoryMap.baby_card_id,
            BabyCategory.baby_category_id,
            BabyCategory.name,
        )
        .join(BabyCategory, BabyCategory.baby_category_id == BabyCardCategoryMap.baby_category_id)
        .filter(BabyCardCategoryMap.baby_id == baby_id)
        .all()
    )
    bc_cat_by_bcid: dict[int, tuple[int, str]] = {
        r.baby_card_id: (r.baby_category_id, r.name) for r in bc_cat_rows
    }

    # 아동에게 활성화된 카테고리 (마스터 카드 fallback 시 baby_category_id 매핑용)
    baby_category_by_master_id: dict[int, tuple[int, str]] = {
        r.category_id: (r.baby_category_id, r.name)
        for r in db.query(BabyCategory).filter(
            BabyCategory.baby_id == baby_id, BabyCategory.is_enabled.is_(True)
        )
        if r.category_id is not None
    }

    # card_id -> (baby_category_id|None, category_name)  from card_master mapping
    master_cat_rows = (
        db.query(
            CardCategoryMapMaster.card_id,
            CategoryMaster.category_id,
            CategoryMaster.name,
            CardCategoryMapMaster.is_primary,
        )
        .join(CategoryMaster, CategoryMaster.category_id == CardCategoryMapMaster.category_id)
        .filter(CardCategoryMapMaster.is_active.is_(True))
        .all()
    )
    master_cat_by_cid: dict[int, tuple[int | None, str]] = {}
    for row in master_cat_rows:
        # is_primary 우선 (현재 시드는 카드당 카테고리 1개라 단순 setdefault로 충분)
        if row.card_id in master_cat_by_cid and not row.is_primary:
            continue
        bcat = baby_category_by_master_id.get(row.category_id)
        master_cat_by_cid[row.card_id] = (
            (bcat[0] if bcat else None),
            bcat[1] if bcat else row.name,
        )

    result: list[CardOut] = []

    for card in baby_cards:
        cat = bc_cat_by_bcid.get(card.baby_card_id)
        if cat is None and card.card_id is not None:
            cat = master_cat_by_cid.get(card.card_id)
        bcid, cname = (cat or (None, None))
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
                category=cname,
                baby_category_id=bcid,
            )
        )

    for cm in master_cards:
        cat = master_cat_by_cid.get(cm.card_id)
        bcid, cname = (cat or (None, None))
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
                category=cname,
                baby_category_id=bcid,
            )
        )

    return SuccessResponse(data=result, message="카드 목록을 조회했습니다.")
