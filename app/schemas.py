from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """공통 성공 응답 래퍼. `data` 는 엔드포인트마다 타입이 다르다.

    각 라우터는 `response_model=SuccessResponse[SomeModel]` 로 선언해
    Swagger 에 `data` 의 실제 구조가 노출되도록 한다.
    """

    success: bool = True
    data: T
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


class CreateCustomCardRequest(BaseModel):
    baby_id: int
    text: str = Field(..., min_length=1, max_length=255)
    part_of_speech: Optional[str] = Field(default="noun", max_length=20)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_favorite: bool = False
    category_name: Optional[str] = Field(default=None, max_length=100)
    baby_category_id: Optional[int] = None


class UpdateCardRequest(BaseModel):
    text: Optional[str] = Field(default=None, min_length=1, max_length=255)
    part_of_speech: Optional[str] = Field(default=None, max_length=20)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_favorite: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None
    category_name: Optional[str] = Field(default=None, max_length=100)
    baby_category_id: Optional[int] = None


class FavoriteUpdateRequest(BaseModel):
    is_favorite: bool


class CategoryOut(BaseModel):
    baby_category_id: int
    category_id: Optional[int] = None
    name: str
    icon_url: Optional[str] = None
    is_enabled: bool = True
    is_favorite: bool = False


class CategoryCardsOut(BaseModel):
    baby_category_id: int
    category_name: str
    cards: list["CardOut"]


class RecommendationRequest(BaseModel):
    baby_id: int
    selected_baby_card_id: Optional[int] = None
    selected_card_id: Optional[int] = None   # 공용(마스터) 카드 선택 시


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


class BabySettingsOut(BaseModel):
    baby_id: int
    parent_pin_enabled: bool
    tts_voice: str
    tts_speed: float
    reward_enabled: bool
    communication_level: Optional[str] = None
    favorite_topics: list[str] = Field(default_factory=list)
    sensory_notes: Optional[str] = None
    avatar_name: Optional[str] = None


class UpdateBabySettingsRequest(BaseModel):
    parent_pin: Optional[str] = Field(default=None, max_length=20)
    tts_voice: Optional[str] = Field(default=None, max_length=50)
    tts_speed: Optional[float] = Field(default=None, ge=0.5, le=2.0)
    reward_enabled: Optional[bool] = None
    communication_level: Optional[str] = Field(default=None, max_length=50)
    favorite_topics: Optional[list[str]] = None
    sensory_notes: Optional[str] = None
    avatar_name: Optional[str] = Field(default=None, max_length=100)


class MyPageSummaryData(BaseModel):
    baby: BabyOut
    settings: BabySettingsOut
    total_cards: int
    favorite_cards: int
    total_logs: int
    total_sentences: int
    latest_sentence: Optional[str] = None


class TopWordOut(BaseModel):
    text: str
    count: int


class ReportSummaryData(BaseModel):
    baby_id: int
    period_days: int
    total_selections: int
    unique_words: int
    total_sentences: int
    average_sentence_length: float
    top_words: list[TopWordOut]
    emotion_counts: dict[str, int]
    recent_sentences: list[str]
    insight: str


class BadgeOut(BaseModel):
    key: str
    title: str
    earned: bool
    description: str


class RewardsData(BaseModel):
    baby_id: int
    reward_enabled: bool
    points: int
    level: int
    badges: list[BadgeOut]


class ParentAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_id: int
    baby_id: int
    parent_name: str
    email: str
    is_active: bool
    created_at: datetime


class RegisterParentRequest(BaseModel):
    baby_id: int
    parent_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class AuthSessionData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    parent: ParentAccountOut


class LogoutData(BaseModel):
    logged_out: bool


class PinVerifyRequest(BaseModel):
    baby_id: int
    pin: str = Field(..., min_length=4, max_length=20)


class PinVerifyData(BaseModel):
    baby_id: int
    verified: bool


class SuggestWordsRequest(BaseModel):
    """부모 단어추가용: 입력 텍스트와 관련된 'DB 에 없는' 새 단어 제안."""

    text: str = Field(..., min_length=1)
    baby_id: Optional[int] = None
    count: int = 6


class SuggestedWord(BaseModel):
    text: str
    pos: Optional[str] = None


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
    favorite_color: Optional[str] = None   # 아이가 좋아하는 색 → 캐릭터 셔츠(pink/blue/green...)
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


# =======================================================
# SuccessResponse.data 전용 타입 (Swagger 노출용)
# =======================================================
class HealthData(BaseModel):
    status: str


class SuggestionsData(BaseModel):
    """`POST /cards/suggest` 의 data."""
    text: str
    suggestions: list[SuggestedWord]


class ImageResult(BaseModel):
    """AI 서버에서 프록시된 Stable Diffusion 결과. 키 미설정 시 image_url=null."""
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    scene: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class AudioResult(BaseModel):
    """AI 서버에서 프록시된 Clova Voice 결과. 키 미설정 시 audio_url=null."""
    audio_url: Optional[str] = None
    audio_path: Optional[str] = None
    params: Optional[dict[str, Any]] = None
    status: Optional[str] = None


class AvatarResult(BaseModel):
    emotion: Optional[str] = None
    image_url: Optional[str] = None


class GeneratedExpressionData(BaseModel):
    """`POST /expressions/generate` 의 data — 멀티모달 '말하기' 결과."""
    baby_id: int
    sentence: str
    image: ImageResult
    audio: AudioResult
    avatar: AvatarResult
    saved: bool = False
    sentence_id: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "baby_id": 5,
                "sentence": "물을 마시고 싶어요.",
                "image": {"image_url": "http://127.0.0.1:8001/generated/images/img_123.png", "status": "generated"},
                "audio": {"audio_url": "http://127.0.0.1:8001/generated/audio/tts_5_ab.mp3", "status": "generated"},
                "avatar": {"emotion": "happy", "image_url": None},
                "saved": True,
                "sentence_id": 41,
            }
        }
    )
