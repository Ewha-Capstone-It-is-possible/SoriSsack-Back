from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BabyAppSettings, BabyBasicInformation
from app.schemas import BabySettingsOut, SuccessResponse, UpdateBabySettingsRequest


router = APIRouter(prefix="/settings", tags=["settings"])


def _serialize_topics(raw_topics: Optional[str]) -> list[str]:
    if not raw_topics:
        return []
    return [item.strip() for item in raw_topics.split(",") if item.strip()]


def _settings_out(baby_id: int, settings: Optional[BabyAppSettings]) -> BabySettingsOut:
    if settings is None:
        return BabySettingsOut(
            baby_id=baby_id,
            parent_pin_enabled=False,
            tts_voice="nara",
            tts_speed=1.0,
            reward_enabled=True,
            communication_level=None,
            favorite_topics=[],
            sensory_notes=None,
            avatar_name=None,
        )

    return BabySettingsOut(
        baby_id=baby_id,
        parent_pin_enabled=bool(settings.parent_pin),
        tts_voice=settings.tts_voice,
        tts_speed=settings.tts_speed,
        reward_enabled=settings.reward_enabled,
        communication_level=settings.communication_level,
        favorite_topics=_serialize_topics(settings.favorite_topics),
        sensory_notes=settings.sensory_notes,
        avatar_name=settings.avatar_name,
    )


@router.get(
    "/{baby_id}",
    response_model=SuccessResponse[BabySettingsOut],
    summary="아동 앱 설정 조회",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
def get_settings(baby_id: int, db: Session = Depends(get_db)):
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    return SuccessResponse(
        data=_settings_out(baby_id, baby.app_settings),
        message="아동 앱 설정을 조회했습니다.",
    )


@router.put(
    "/{baby_id}",
    response_model=SuccessResponse[BabySettingsOut],
    summary="아동 앱 설정 저장",
    responses={404: {"description": "아동 정보를 찾을 수 없습니다."}},
)
def update_settings(
    baby_id: int,
    payload: UpdateBabySettingsRequest,
    db: Session = Depends(get_db),
):
    baby = db.get(BabyBasicInformation, baby_id)
    if baby is None:
        raise HTTPException(status_code=404, detail="아동 정보를 찾을 수 없습니다.")

    settings = baby.app_settings
    if settings is None:
        settings = BabyAppSettings(baby_id=baby_id)
        db.add(settings)

    if payload.parent_pin is not None:
        settings.parent_pin = payload.parent_pin
    if payload.tts_voice is not None:
        settings.tts_voice = payload.tts_voice
    if payload.tts_speed is not None:
        settings.tts_speed = payload.tts_speed
    if payload.reward_enabled is not None:
        settings.reward_enabled = payload.reward_enabled
    if payload.communication_level is not None:
        settings.communication_level = payload.communication_level
    if payload.favorite_topics is not None:
        settings.favorite_topics = ", ".join(
            item.strip() for item in payload.favorite_topics if item.strip()
        )
    if payload.sensory_notes is not None:
        settings.sensory_notes = payload.sensory_notes
    if payload.avatar_name is not None:
        settings.avatar_name = payload.avatar_name

    db.commit()
    db.refresh(settings)

    return SuccessResponse(
        data=_settings_out(baby_id, settings),
        message="아동 앱 설정을 저장했습니다.",
    )
