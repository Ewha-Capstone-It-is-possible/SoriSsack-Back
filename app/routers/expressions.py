from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_parent, get_owned_baby
from app.db import get_db
from app.models import Parent, SentenceMaster
from app.schemas import (
    CreateSentenceRequest,
    GeneratedExpressionData,
    SentenceGenerateRequest,
    SentenceOut,
    SuccessResponse,
)
from app.services.ai_client import fetch_sentence


router = APIRouter(prefix="/expressions", tags=["expressions"])


@router.post(
    "",
    response_model=SuccessResponse[SentenceOut],
    summary="문장 저장 (로그인 필요)",
    description="이미 만들어진 문장 결과를 sentence_master 에 저장한다.",
    responses={
        403: {"description": "이 아동에 접근할 권한이 없습니다."},
        404: {"description": "아동 정보를 찾을 수 없습니다."},
    },
)
def create_expression(
    payload: CreateSentenceRequest,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    get_owned_baby(payload.baby_id, parent, db)

    sentence = SentenceMaster(**payload.model_dump())
    db.add(sentence)
    db.commit()
    db.refresh(sentence)

    return SuccessResponse(
        data=SentenceOut.model_validate(sentence),
        message="문장 생성 결과를 저장했습니다.",
    )


@router.post(
    "/generate",
    response_model=SuccessResponse[GeneratedExpressionData],
    summary="말하기: 문장 + 이미지 + 음성 생성 (로그인 필요)",
    description="선택 단어 배열을 AI 서버로 보내 문장·이미지·음성을 생성하고 sentence_master 에 저장.",
    responses={
        403: {"description": "이 아동에 접근할 권한이 없습니다."},
        404: {"description": "아동 정보를 찾을 수 없습니다."},
    },
)
async def generate_expression(
    payload: SentenceGenerateRequest,
    parent: Parent = Depends(get_current_parent),
    db: Session = Depends(get_db),
):
    """
    멀티모달 '말하기': 선택 단어 배열을 AI 서버로 보내 자연스러운 문장 + 이미지 + 음성을
    생성하고(없으면 graceful fallback), 결과를 sentence_master 에 저장한다.
    """
    get_owned_baby(payload.baby_id, parent, db)

    result = await fetch_sentence(payload)

    saved = False
    if payload.save and result.get("sentence"):
        sentence = SentenceMaster(
            baby_id=payload.baby_id,
            sentence_text=result["sentence"],
            played_tts=bool((result.get("audio") or {}).get("audio_url")),
            avatar_image_url=(result.get("image") or {}).get("image_url"),
            avatar_audio_url=(result.get("audio") or {}).get("audio_url"),
        )
        db.add(sentence)
        db.commit()
        db.refresh(sentence)
        result["sentence_id"] = sentence.sentence_id
        saved = True

    result["saved"] = saved
    return SuccessResponse(
        data=result,
        message="멀티모달 문장 생성 결과입니다.",
    )
