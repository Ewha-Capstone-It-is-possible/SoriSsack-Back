from datetime import datetime

from app.db import Base, SessionLocal, engine
from app.models import BabyBasicInformation, BabyCard, CardMaster


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing_baby = db.query(BabyBasicInformation).filter(BabyBasicInformation.baby_id == 1).first()
    if existing_baby:
        db.close()
        return

    baby = BabyBasicInformation(
        baby_id=1,
        name="민수",
        age=7,
        development_stage="초기 문장 단계",
        preferred_tts_voice="female",
        preferred_tts_speed=1.0,
    )

    card_1 = CardMaster(
        card_id=1,
        base_text="사과",
        normalized_text="사과",
        part_of_speech="Noun",
        default_image_url=None,
    )
    card_2 = CardMaster(
        card_id=2,
        base_text="물",
        normalized_text="물",
        part_of_speech="Noun",
        default_image_url=None,
    )
    card_3 = CardMaster(
        card_id=3,
        base_text="주세요",
        normalized_text="주세요",
        part_of_speech="verb",
        default_image_url=None,
    )

    baby_card_1 = BabyCard(
        baby_card_id=101,
        baby_id=1,
        card_id=1,
        text=None,
        type=None,
        custom_image_url=None,
        is_favorite=True,
        source="system_default",
        status="default",
        usage_count=3,
        last_used_at=datetime.utcnow(),
        is_active=True,
    )

    db.add_all([baby, card_1, card_2, card_3, baby_card_1])
    db.commit()
    db.close()


if __name__ == "__main__":
    seed()
