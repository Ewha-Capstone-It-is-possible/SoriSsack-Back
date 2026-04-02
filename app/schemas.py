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
    name: str
    age: int
    development_stage: Optional[str] = None
    preferred_tts_voice: Optional[str] = None
    preferred_tts_speed: Optional[float] = None
    created_at: datetime
    updated_at: datetime


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


class RecommendationRequest(BaseModel):
    baby_id: int
    selected_baby_card_id: int


class RecommendedWord(BaseModel):
    baby_card_id: Optional[int] = None
    card_id: Optional[int] = None
    text: str
    pos: Optional[str] = None
    system_score: Optional[float] = None


class RecommendationResult(BaseModel):
    baby_id: int
    selected_word: str
    recommended_words: list[RecommendedWord]


class CreateSentenceRequest(BaseModel):
    baby_id: int
    sentence_text: str = Field(..., min_length=1)
    played_tts: bool = False
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    avatar_video_url: Optional[str] = None


class SentenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sentence_id: int
    baby_id: int
    sentence_text: str
    played_tts: bool
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    avatar_video_url: Optional[str] = None
    created_at: datetime


class CreateVocabLogRequest(BaseModel):
    baby_id: int
    baby_card_id: Optional[int] = None
    card_id: Optional[int] = None
    text: str = Field(..., min_length=1)
    context_json: Optional[dict[str, Any]] = None
    used_at: datetime


class VocabLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: int
    baby_id: int
    baby_card_id: Optional[int] = None
    card_id: Optional[int] = None
    text: str
    context_json: Optional[dict[str, Any]] = None
    used_at: datetime
    created_at: datetime
