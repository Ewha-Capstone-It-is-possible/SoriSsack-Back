from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyBasicInformation, SentenceMaster
from app.schemas import CreateSentenceRequest, SentenceOut, SuccessResponse


router = APIRouter(prefix="/expressions", tags=["expressions"])


@router.post("", response_model=SuccessResponse)
def create_expression(payload: CreateSentenceRequest, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, payload.baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    sentence = SentenceMaster(**payload.model_dump())
    db.add(sentence)
    db.commit()
    db.refresh(sentence)

    return SuccessResponse(
        data=SentenceOut.model_validate(sentence),
        message="문장 생성 결과를 저장했습니다.",
    )
