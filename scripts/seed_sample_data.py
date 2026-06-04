"""
scripts/seed_sample_data.py
---------------------------
데모용 시드 데이터 적재.

AI 서버(sorisak-ai)의 공유 단어 사전(card_master 95개)·아동 5명·baby_card 100개와
**동일한 ID**로 백엔드 DB를 채운다. 이렇게 하면:

  - 프론트가 `GET /cards/{baby_id}` 로 받는 카드 목록과
  - AI `/recommend` 가 돌려주는 추천 단어(baby_card_id / card_id / text)

가 같은 네임스페이스를 공유하므로, 추천 결과가 프론트 카드와 정확히 매칭되어
화면에 그대로 렌더링된다. (FE는 baby_card_id → card_id → text 순으로 매칭)

데이터 원본: scripts/seed_data.json  (AI dummy_data 에서 추출, 커밋된 산출물)

실행:
    python3 -m scripts.seed_sample_data
"""

import json
from datetime import datetime
from pathlib import Path

from app.db import Base, SessionLocal, engine
from app.models import (
    BabyBasicInformation,
    BabyCard,
    BabyCardCategoryMap,
    BabyCategory,
    CardCategoryMapMaster,
    CardMaster,
    CategoryMaster,
)

SEED_PATH = Path(__file__).with_name("seed_data.json")


def _load_seed() -> dict:
    with SEED_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def seed() -> None:
    data = _load_seed()
    now = datetime.now()

    # 데모 시드는 결정론적으로 다시 깔리도록 drop → create
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1) 공용 카테고리 사전
        for c in data["categories"]:
            db.add(
                CategoryMaster(
                    category_id=c["category_id"],
                    name=c["name"],
                    icon_url=c.get("icon_url"),
                    is_active=True,
                )
            )

        # 2) 공용 단어 사전 (card_master)
        for c in data["card_master"]:
            db.add(
                CardMaster(
                    card_id=c["card_id"],
                    base_text=c["base_text"],
                    normalized_text=c["normalized_text"],
                    part_of_speech=c["part_of_speech"] or "noun",
                    default_image_url=None,
                    is_active=True,
                )
            )

        # 3) card_master ↔ category 매핑
        for m in data["card_category_map"]:
            db.add(
                CardCategoryMapMaster(
                    card_id=m["card_id"],
                    category_id=m["category_id"],
                    is_primary=m.get("is_primary", True),
                    is_active=True,
                )
            )

        # 4) 아동 기본 정보
        for b in data["babies"]:
            db.add(
                BabyBasicInformation(
                    baby_id=b["baby_id"],
                    baby_name=b["baby_name"],
                    sex=b["sex"],
                    birth=datetime.fromisoformat(b["birth"]),
                )
            )

        db.flush()

        # 5) 아동별 카테고리 (baby_category) — 공용 카테고리를 아동별로 복제
        #    {(baby_id, category_id): baby_category_id}
        baby_category_id_by_key: dict[tuple[int, int], int] = {}
        for b in data["babies"]:
            for c in data["categories"]:
                bc = BabyCategory(
                    baby_id=b["baby_id"],
                    category_id=c["category_id"],
                    name=c["name"],
                    icon_url=c.get("icon_url"),
                    is_enabled=True,
                    is_favorite=False,
                )
                db.add(bc)
                db.flush()
                baby_category_id_by_key[(b["baby_id"], c["category_id"])] = bc.baby_category_id

        # 6) baby_card + baby_card ↔ category 매핑
        for c in data["baby_cards"]:
            db.add(
                BabyCard(
                    baby_card_id=c["baby_card_id"],
                    baby_id=c["baby_id"],
                    card_id=c.get("card_id"),
                    text=c.get("text"),
                    part_of_speech=c.get("part_of_speech"),
                    custom_image_url=None,
                    is_favorite=c.get("is_favorite", False),
                    source=c.get("source", "system_default"),
                    status=c.get("status", "default"),
                    usage_count=c.get("usage_count", 0),
                    last_used_at=now,
                    is_active=True,
                )
            )
            baby_category_id = baby_category_id_by_key.get(
                (c["baby_id"], c["category_id"])
            )
            if baby_category_id is not None:
                db.add(
                    BabyCardCategoryMap(
                        baby_id=c["baby_id"],
                        baby_card_id=c["baby_card_id"],
                        baby_category_id=baby_category_id,
                    )
                )

        db.commit()

        print(
            "Seed done.\n"
            f"  categories : {len(data['categories'])}\n"
            f"  card_master: {len(data['card_master'])}\n"
            f"  babies     : {[b['baby_id'] for b in data['babies']]}\n"
            f"  baby_cards : {len(data['baby_cards'])}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
