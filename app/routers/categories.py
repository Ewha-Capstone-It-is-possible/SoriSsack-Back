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
    Parent,
)
from app.schemas import CardCategoryOut, CardOut, CategoryCardsOut, CategoryOut, SuccessResponse


router = APIRouter(prefix="/categories", tags=["categories"])


def _category_out_from_baby_category(bcat: BabyCategory) -> CardCategoryOut:
    return CardCategoryOut(
        baby_category_id=bcat.baby_category_id,
        category_id=bcat.category_id,
        name=bcat.name,
        icon_url=bcat.icon_url,
    )


@router.get(
    "/{baby_id}",
    response_model=SuccessResponse[list[CategoryOut]],
    summary="아동 카테고리 목록 (로그인 필요)",
    responses={
        403: {"description": "이 아동에 접근할 권한이 없습니다."},
        404: {"description": "아동 정보를 찾을 수 없습니다."},
    },
)
def list_categories(
    baby_id: int,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """아동에게 활성화된 카테고리 목록."""
    get_owned_baby(baby_id, parent, db)

    rows = (
        db.query(BabyCategory)
        .filter(BabyCategory.baby_id == baby_id, BabyCategory.is_enabled.is_(True))
        .order_by(BabyCategory.manual_order.nullslast(), BabyCategory.baby_category_id)
        .all()
    )

    result = [
        CategoryOut(
            baby_category_id=r.baby_category_id,
            category_id=r.category_id,
            name=r.name,
            icon_url=r.icon_url,
            is_enabled=r.is_enabled,
            is_favorite=r.is_favorite,
        )
        for r in rows
    ]
    return SuccessResponse(data=result, message="카테고리 목록을 조회했습니다.")


@router.get(
    "/{baby_id}/{baby_category_id}/cards",
    response_model=SuccessResponse[CategoryCardsOut],
    summary="카테고리별 카드 목록 (로그인 필요)",
    responses={
        403: {"description": "이 아동에 접근할 권한이 없습니다."},
        404: {"description": "아동/카테고리를 찾을 수 없습니다."},
    },
)
def cards_in_category(
    baby_id: int,
    baby_category_id: int,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """카테고리에 속한 카드. 개인 카드 우선, 부족분은 card_master fallback."""
    get_owned_baby(baby_id, parent, db)

    bcat = db.get(BabyCategory, baby_category_id)
    if bcat is None or bcat.baby_id != baby_id:
        raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")

    category = _category_out_from_baby_category(bcat)

    # 1) 개인 카드
    personal_rows = (
        db.query(BabyCard)
        .join(BabyCardCategoryMap, BabyCardCategoryMap.baby_card_id == BabyCard.baby_card_id)
        .filter(
            BabyCardCategoryMap.baby_id == baby_id,
            BabyCardCategoryMap.baby_category_id == baby_category_id,
            BabyCard.is_active.is_(True),
            BabyCard.status != "off",
        )
        .all()
    )

    cards: list[CardOut] = []
    used_card_ids: set[int] = set()
    for bc in personal_rows:
        cm = bc.card_master
        if bc.card_id is not None:
            used_card_ids.add(bc.card_id)
        cards.append(
            CardOut(
                baby_card_id=bc.baby_card_id,
                card_id=bc.card_id,
                text=bc.text or (cm.base_text if cm else ""),
                part_of_speech=bc.part_of_speech or (cm.part_of_speech if cm else None),
                image_url=bc.custom_image_url or (cm.default_image_url if cm else None),
                is_favorite=bc.is_favorite,
                source=bc.source,
                status=bc.status,
                usage_count=bc.usage_count,
                category=category,
            )
        )

    # 2) card_master fallback (같은 category_id, 아직 개인화 안 된 카드)
    if bcat.category_id is not None:
        master_q = (
            db.query(CardMaster)
            .join(CardCategoryMapMaster, CardCategoryMapMaster.card_id == CardMaster.card_id)
            .filter(
                CardCategoryMapMaster.category_id == bcat.category_id,
                CardCategoryMapMaster.is_active.is_(True),
                CardMaster.is_active.is_(True),
            )
        )
        if used_card_ids:
            master_q = master_q.filter(~CardMaster.card_id.in_(used_card_ids))
        for cm in master_q.all():
            cards.append(
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
                    category=category,
                )
            )

    return SuccessResponse(
        data=CategoryCardsOut(
            baby_category_id=baby_category_id,
            category_name=bcat.name,
            cards=cards,
        ),
        message="카테고리 카드 목록을 조회했습니다.",
    )
