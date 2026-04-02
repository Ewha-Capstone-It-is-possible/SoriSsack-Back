from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyBasicInformation, BabyCard, BabyVocabLog
from app.schemas import CreateVocabLogRequest, SuccessResponse, VocabLogOut


router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", response_model=SuccessResponse)
def create_vocab_log(payload: CreateVocabLogRequest, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, payload.baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    if payload.baby_card_id is not None:
        baby_card = db.get(BabyCard, payload.baby_card_id)
        if baby_card is None or baby_card.baby_id != payload.baby_id:
            raise HTTPException(status_code=404, detail="선택한 아동 카드를 찾을 수 없습니다.")

        baby_card.usage_count += 1
        baby_card.last_used_at = payload.used_at

    log = BabyVocabLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)

    return SuccessResponse(
        data=VocabLogOut.model_validate(log),
        message="단어 사용 로그를 저장했습니다.",
    )
