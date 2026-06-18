from typing import Optional

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
from app.schemas import (
    CardCategoryOut,
    CardOut,
    CreateCustomCardRequest,
    FavoriteUpdateRequest,
    SuccessResponse,
    SuggestionsData,
    SuggestWordsRequest,
    UpdateCardRequest,
)
from app.services.ai_client import fetch_card_image, fetch_related_words


router = APIRouter(prefix="/cards", tags=["cards"])


def _get_baby_or_404(baby_id: int, db: Session) -> BabyBasicInformation:
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")
    return baby


def _get_or_create_baby_category(
    *,
    db: Session,
    baby_id: int,
    baby_category_id: Optional[int],
    category_name: Optional[str],
) -> Optional[BabyCategory]:
    if baby_category_id is not None:
        baby_category = db.get(BabyCategory, baby_category_id)
        if baby_category is None or baby_category.baby_id != baby_id:
            raise HTTPException(status_code=404, detail="카테고리를 찾을 수 없습니다.")
        return baby_category

    if not category_name:
        return None

    cleaned_name = category_name.strip()
    if not cleaned_name:
        return None

    existing = (
        db.query(BabyCategory)
        .filter(BabyCategory.baby_id == baby_id, BabyCategory.name == cleaned_name)
        .first()
    )
    if existing is not None:
        return existing

    master_category = (
        db.query(CategoryMaster)
        .filter(CategoryMaster.name == cleaned_name, CategoryMaster.is_active.is_(True))
        .first()
    )

    baby_category = BabyCategory(
        baby_id=baby_id,
        category_id=master_category.category_id if master_category else None,
        name=cleaned_name,
        icon_url=master_category.icon_url if master_category else None,
        is_enabled=True,
        is_favorite=False,
    )
    db.add(baby_category)
    db.flush()
    return baby_category


def _upsert_card_category_map(
    *,
    db: Session,
    baby_id: int,
    baby_card_id: int,
    baby_category: Optional[BabyCategory],
) -> None:
    existing_map = (
        db.query(BabyCardCategoryMap)
        .filter(
            BabyCardCategoryMap.baby_id == baby_id,
            BabyCardCategoryMap.baby_card_id == baby_card_id,
        )
        .first()
    )

    if baby_category is None:
        if existing_map is not None:
            db.delete(existing_map)
        return

    if existing_map is None:
        db.add(
            BabyCardCategoryMap(
                baby_id=baby_id,
                baby_card_id=baby_card_id,
                baby_category_id=baby_category.baby_category_id,
            )
        )
        return

    existing_map.baby_category_id = baby_category.baby_category_id


def _resolve_card_category(
    *,
    db: Session,
    baby_id: int,
    baby_card: BabyCard,
) -> Optional[CardCategoryOut]:
    baby_map = (
        db.query(BabyCardCategoryMap)
        .join(BabyCategory, BabyCategory.baby_category_id == BabyCardCategoryMap.baby_category_id)
        .filter(
            BabyCardCategoryMap.baby_id == baby_id,
            BabyCardCategoryMap.baby_card_id == baby_card.baby_card_id,
        )
        .first()
    )
    if baby_map is not None:
        baby_category = baby_map.baby_category
        return CardCategoryOut(
            baby_category_id=baby_category.baby_category_id,
            category_id=baby_category.category_id,
            name=baby_category.name,
            icon_url=baby_category.icon_url,
        )

    if baby_card.card_id is None:
        return None

    master_map = (
        db.query(CardCategoryMapMaster, CategoryMaster)
        .join(CategoryMaster, CategoryMaster.category_id == CardCategoryMapMaster.category_id)
        .filter(
            CardCategoryMapMaster.card_id == baby_card.card_id,
            CardCategoryMapMaster.is_active.is_(True),
        )
        .order_by(CardCategoryMapMaster.is_primary.desc())
        .first()
    )
    if master_map is None:
        return None

    _, category = master_map
    return CardCategoryOut(
        baby_category_id=None,
        category_id=category.category_id,
        name=category.name,
        icon_url=category.icon_url,
    )


def _card_out_from_baby_card(
    *,
    db: Session,
    baby_id: int,
    baby_card: BabyCard,
) -> CardOut:
    master = baby_card.card_master
    return CardOut(
        baby_card_id=baby_card.baby_card_id,
        card_id=baby_card.card_id,
        text=baby_card.text or (master.base_text if master else ""),
        part_of_speech=baby_card.part_of_speech or (master.part_of_speech if master else None),
        image_url=baby_card.custom_image_url or (master.default_image_url if master else None),
        is_favorite=baby_card.is_favorite,
        source=baby_card.source,
        status=baby_card.status,
        usage_count=baby_card.usage_count,
        category=_resolve_card_category(db=db, baby_id=baby_id, baby_card=baby_card),
    )


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


@router.post(
    "",
    response_model=SuccessResponse[CardOut],
    summary="사용자 정의 카드 생성",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
async def create_custom_card(payload: CreateCustomCardRequest, db: Session = Depends(get_db)):
    _get_baby_or_404(payload.baby_id, db)

    baby_card = BabyCard(
        baby_id=payload.baby_id,
        card_id=None,
        text=payload.text.strip(),
        part_of_speech=payload.part_of_speech,
        custom_image_url=payload.image_url,
        is_favorite=payload.is_favorite,
        source="parent_manual",
        status="add",
        is_active=True,
    )
    db.add(baby_card)
    db.flush()

    # 이미지 미지정 시: 아이별 개인화 이미지를 AI(SD)로 생성 → 아이모드 카드에 표시
    if not payload.image_url:
        generated_url = await fetch_card_image(baby_card.text, payload.baby_id)
        if generated_url:
            baby_card.custom_image_url = generated_url

    baby_category = _get_or_create_baby_category(
        db=db,
        baby_id=payload.baby_id,
        baby_category_id=payload.baby_category_id,
        category_name=payload.category_name,
    )
    _upsert_card_category_map(
        db=db,
        baby_id=payload.baby_id,
        baby_card_id=baby_card.baby_card_id,
        baby_category=baby_category,
    )

    db.commit()
    db.refresh(baby_card)

    return SuccessResponse(
        data=_card_out_from_baby_card(db=db, baby_id=payload.baby_id, baby_card=baby_card),
        message="사용자 정의 카드를 생성했습니다.",
    )


@router.patch(
    "/{baby_card_id}",
    response_model=SuccessResponse[CardOut],
    summary="아동 카드 수정",
    responses={404: {"description": "아동 카드 정보를 찾을 수 없습니다."}},
)
def update_card(baby_card_id: int, payload: UpdateCardRequest, db: Session = Depends(get_db)):
    baby_card = db.get(BabyCard, baby_card_id)
    if baby_card is None:
        raise HTTPException(status_code=404, detail="아동 카드를 찾을 수 없습니다.")

    if payload.text is not None:
        baby_card.text = payload.text.strip()
    if payload.part_of_speech is not None:
        baby_card.part_of_speech = payload.part_of_speech
    if payload.image_url is not None:
        baby_card.custom_image_url = payload.image_url
    if payload.is_favorite is not None:
        baby_card.is_favorite = payload.is_favorite
    if payload.status is not None:
        baby_card.status = payload.status
    if payload.is_active is not None:
        baby_card.is_active = payload.is_active

    if payload.baby_category_id is not None or payload.category_name is not None:
        baby_category = _get_or_create_baby_category(
            db=db,
            baby_id=baby_card.baby_id,
            baby_category_id=payload.baby_category_id,
            category_name=payload.category_name,
        )
        _upsert_card_category_map(
            db=db,
            baby_id=baby_card.baby_id,
            baby_card_id=baby_card.baby_card_id,
            baby_category=baby_category,
        )

    db.commit()
    db.refresh(baby_card)

    return SuccessResponse(
        data=_card_out_from_baby_card(db=db, baby_id=baby_card.baby_id, baby_card=baby_card),
        message="아동 카드 정보를 수정했습니다.",
    )


@router.patch(
    "/{baby_card_id}/favorite",
    response_model=SuccessResponse[CardOut],
    summary="즐겨찾기 카드 여부 변경",
    responses={404: {"description": "아동 카드 정보를 찾을 수 없습니다."}},
)
def update_favorite(
    baby_card_id: int,
    payload: FavoriteUpdateRequest,
    db: Session = Depends(get_db),
):
    baby_card = db.get(BabyCard, baby_card_id)
    if baby_card is None:
        raise HTTPException(status_code=404, detail="아동 카드를 찾을 수 없습니다.")

    baby_card.is_favorite = payload.is_favorite
    db.commit()
    db.refresh(baby_card)

    return SuccessResponse(
        data=_card_out_from_baby_card(db=db, baby_id=baby_card.baby_id, baby_card=baby_card),
        message="즐겨찾기 상태를 변경했습니다.",
    )


@router.get(
    "/{baby_id}",
    response_model=SuccessResponse[list[CardOut]],
    summary="아동 카드 목록 조회",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
def get_cards(baby_id: int, db: Session = Depends(get_db)):
    _get_baby_or_404(baby_id, db)

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
