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


# =======================================================
# 인증 (회원가입 / 로그인 / 카카오)
# =======================================================
class SignupRequest(BaseModel):
    parent_name: str = Field(..., min_length=1, description="부모 이름")
    user_id: str = Field(..., min_length=4, max_length=50, description="로그인 아이디")
    password: str = Field(..., min_length=4, description="비밀번호")
    email: Optional[str] = Field(None, description="이메일")
    phone_number: Optional[str] = Field(None, description="핸드폰 번호")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent_name": "홍길동",
                "user_id": "gildong01",
                "password": "secret123",
                "email": "gildong@example.com",
                "phone_number": "010-1234-5678",
            }
        }
    )


class LoginRequest(BaseModel):
    user_id: str = Field(..., description="로그인 아이디")
    password: str = Field(..., description="비밀번호")

    model_config = ConfigDict(
        json_schema_extra={"example": {"user_id": "gildong01", "password": "secret123"}}
    )


class KakaoLoginRequest(BaseModel):
    """카카오 로그인: 프론트가 카카오 SDK 로 받은 access token 을 전달."""
    kakao_access_token: str = Field(..., description="카카오 SDK 가 발급한 access token")


class CheckIdData(BaseModel):
    user_id: str
    available: bool  # True=사용 가능(중복 없음)


class ParentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parent_id: int
    user_id: Optional[str] = None
    parent_name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    provider: str


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    parent: ParentOut


class CreateBabyRequest(BaseModel):
    """온보딩: 로그인한 부모가 자기 아이를 등록."""
    baby_name: str = Field(..., min_length=1)
    sex: str = Field(..., min_length=1, max_length=1, description="M | F")
    birth: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"baby_name": "민준", "sex": "M", "birth": "2020-03-15T00:00:00"}
        }
    )


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
