from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_owned_baby
from app.db import get_db
from app.models import BabyBasicInformation, Parent
from app.schemas import BabyOut, CreateBabyRequest, SuccessResponse


router = APIRouter(prefix="/children", tags=["children"])


@router.get(
    "",
    response_model=SuccessResponse[list[BabyOut]],
    summary="내 아이 목록 (로그인 필요)",
)
def list_children(
    parent: Parent = Depends(get_current_parent), db: Session = Depends(get_db)
):
    babies = (
        db.query(BabyBasicInformation)
        .filter(BabyBasicInformation.parent_id == parent.parent_id)
        .all()
    )
    return SuccessResponse(
        data=[BabyOut.model_validate(b) for b in babies],
        message="내 아이 목록입니다.",
    )


@router.post(
    "",
    response_model=SuccessResponse[BabyOut],
    summary="아이 등록 (온보딩, 로그인 필요)",
)
def create_child(
    payload: CreateBabyRequest,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    baby = BabyBasicInformation(
        parent_id=parent.parent_id,
        baby_name=payload.baby_name,
        sex=payload.sex,
        birth=payload.birth,
    )
    db.add(baby)
    db.commit()
    db.refresh(baby)
    return SuccessResponse(data=BabyOut.model_validate(baby), message="아이를 등록했습니다.")


@router.get(
    "/{baby_id}",
    response_model=SuccessResponse[BabyOut],
    summary="아동 정보 조회 (로그인 필요)",
    responses={
        403: {"description": "이 아동에 접근할 권한이 없습니다."},
        404: {"description": "아동 정보를 찾을 수 없습니다."},
    },
)
def get_child(
    baby_id: int,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    baby = get_owned_baby(baby_id, parent, db)
    return SuccessResponse(
        data=BabyOut.model_validate(baby),
        message="아동 정보를 조회했습니다.",
    )
