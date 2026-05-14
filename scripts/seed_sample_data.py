from datetime import UTC, datetime

from app.db import Base, SessionLocal, engine
from app.models import BabyBasicInformation, BabyCard, CardMaster


def _ensure(db, model, lookup, defaults=None):
    instance = db.query(model).filter_by(**lookup).first()
    if instance:
        return instance
    instance = model(**{**lookup, **(defaults or {})})
    db.add(instance)
    db.flush()
    return instance


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        baby = _ensure(
            db,
            BabyBasicInformation,
            {"baby_id": 3},
            {"baby_name": "민준", "sex": "M", "birth": datetime(2022, 6, 15)},
        )

        cards = [
            {"base_text": "사과", "normalized_text": "사과", "part_of_speech": "noun"},
            {"base_text": "물", "normalized_text": "물", "part_of_speech": "noun"},
            {"base_text": "주세요", "normalized_text": "주세요", "part_of_speech": "verb"},
        ]
        card_objs = [
            _ensure(db, CardMaster, {"normalized_text": c["normalized_text"]}, c)
            for c in cards
        ]

        existing_bc = db.query(BabyCard).filter_by(baby_id=baby.baby_id).first()
        if not existing_bc:
            db.add(
                BabyCard(
                    baby_id=baby.baby_id,
                    card_id=card_objs[0].card_id,
                    text=None,
                    part_of_speech=None,
                    custom_image_url=None,
                    is_favorite=True,
                    source="system_default",
                    status="default",
                    usage_count=3,
                    last_used_at=datetime.now(UTC),
                    is_active=True,
                )
            )

        db.commit()
        print(
            f"Seed done. baby_id={baby.baby_id}, "
            f"cards={[c.card_id for c in card_objs]}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
