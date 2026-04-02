from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyBasicInformation
from app.schemas import BabyOut, SuccessResponse


router = APIRouter(prefix="/children", tags=["children"])


@router.get("/{baby_id}", response_model=SuccessResponse)
def get_child(baby_id: int, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    return SuccessResponse(
        data=BabyOut.model_validate(baby),
        message="아동 정보를 조회했습니다.",
    )
