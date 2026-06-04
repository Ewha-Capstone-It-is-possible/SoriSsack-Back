from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class SuccessResponse(BaseModel):
    success: bool = True
    data: Any
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class BabyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    baby_id: int
    baby_name: str
    sex: str
    birth: datetime
    created_at: datetime
    updated_at: datetime


class CardCategoryOut(BaseModel):
    baby_category_id: Optional[int] = None
    category_id: Optional[int] = None
    name: str
    icon_url: Optional[str] = None


class CardOut(BaseModel):
    baby_card_id: Optional[int] = None
    card_id: Optional[int] = None
    text: str
    part_of_speech: Optional[str] = None
    image_url: Optional[str] = None
    is_favorite: bool = False
    source: str
    status: str
    usage_count: int = 0
    category: Optional[CardCategoryOut] = None


class RecommendationRequest(BaseModel):
    baby_id: int
    selected_baby_card_id: Optional[int] = None


class RecommendedWord(BaseModel):
    baby_card_id: Optional[int] = None
    card_id: Optional[int] = None
    text: str
    pos: Optional[str] = None
    system_score: float


class RecommendationResult(BaseModel):
    baby_id: int
    selected_word: Optional[str] = None
    recommended_words: list[RecommendedWord]


class CreateSentenceRequest(BaseModel):
    baby_id: int
    sentence_text: str = Field(..., min_length=1)
    played_tts: bool = False
    avatar_image_url: Optional[str] = None
    avatar_audio_url: Optional[str] = None


class SentenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sentence_id: int
    baby_id: int
    sentence_text: str
    played_tts: bool
    avatar_image_url: Optional[str] = None
    avatar_audio_url: Optional[str] = None
    created_at: datetime


class SentenceWordItem(BaseModel):
    text: str
    pos: Optional[str] = None
    baby_card_id: Optional[int] = None
    card_id: Optional[int] = None


class SentenceGenerateRequest(BaseModel):
    """멀티모달 '말하기': 선택 단어 배열 → AI 문장 보정 + 이미지 + 음성."""

    baby_id: int
    words: list[SentenceWordItem] = Field(..., min_length=1)
    emotion: Optional[str] = "neutral"
    save: bool = True   # 생성 결과를 sentence_master 에 저장할지


class CreateVocabLogRequest(BaseModel):
    baby_id: int
    baby_card_id: Optional[int] = None
    card_id: Optional[int] = None
    text_snapshot: str = Field(..., min_length=1)
    context_json: Optional[dict[str, Any]] = None
    used_at: datetime


class VocabLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: int
    baby_id: int
    baby_card_id: Optional[int] = None
    card_id: Optional[int] = None
    text_snapshot: str
    context_json: Optional[dict[str, Any]] = None
    used_at: datetime
    created_at: datetime
