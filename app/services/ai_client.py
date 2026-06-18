"""
app/services/ai_client.py
-------------------------
AI 추론 서버(sorisak-ai, FastAPI) 호출 클라이언트.

  - USE_MOCK_AI=true  → 외부 AI 없이 고정 mock 응답 (프론트 단독 개발용)
  - USE_MOCK_AI=false → AI_SERVER_URL 의 실제 추론 서버 호출

견고성: 실제 호출이 네트워크/오류로 실패하면 mock 으로 graceful fallback 하여
        데모 중 추천 화면이 비지 않도록 한다(로그만 남김).
"""

import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.schemas import (
    RecommendationRequest,
    RecommendationResult,
    RecommendedWord,
    SentenceGenerateRequest,
)

logger = logging.getLogger(__name__)

_AI_TIMEOUT = 30.0


def _mock_recommendation(payload: RecommendationRequest) -> RecommendationResult:
    return RecommendationResult(
        baby_id=payload.baby_id,
        selected_word="mock-selected-word",
        recommended_words=[
            RecommendedWord(baby_card_id=None, card_id=28, text="주세요", pos="verb", system_score=0.95),
            RecommendedWord(baby_card_id=None, card_id=40, text="사주세요", pos="verb", system_score=0.91),
            RecommendedWord(baby_card_id=None, card_id=21, text="좋아", pos="adjective", system_score=0.88),
        ],
    )


async def fetch_recommendations(payload: RecommendationRequest) -> RecommendationResult:
    """선택 카드 기반 추천 단어. AI 서버 → 실패 시 mock fallback."""
    if settings.use_mock_ai:
        return _mock_recommendation(payload)

    try:
        async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
            response = await client.post(
                f"{settings.ai_server_url}/recommend",
                json=payload.model_dump(),
            )
            response.raise_for_status()
            return RecommendationResult(**response.json())
    except Exception as exc:  # 네트워크/타임아웃/파싱 등 → mock 으로 폴백
        logger.warning("AI /recommend 호출 실패, mock 으로 폴백합니다: %s", exc)
        return _mock_recommendation(payload)


def _fallback_sentence(payload: SentenceGenerateRequest, status: str) -> dict:
    texts = [w.text for w in payload.words]
    return {
        "baby_id": payload.baby_id,
        "sentence": " ".join(texts),
        "image": {"image_url": None, "status": status},
        "audio": {"audio_url": None, "status": status},
        "avatar": {"emotion": payload.emotion, "image_url": None},
        "saved": False,
    }


async def fetch_sentence(payload: SentenceGenerateRequest) -> dict:
    """
    멀티모달 문장 생성('말하기'): 선택 단어 배열 → 문장 보정 + 이미지 + 음성.
    AI 서버의 POST /sentence 를 그대로 프록시한다.

    AI 키(OpenAI/Stable Diffusion/Clova)가 없어도 AI 서버가 stub 으로 응답하므로
    항상 동작한다. AI 서버 자체가 꺼져 있으면 단어를 이어 붙인 fallback 문장을 반환.
    """
    if settings.use_mock_ai:
        return _fallback_sentence(payload, "mock")

    try:
        async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
            response = await client.post(
                f"{settings.ai_server_url}/sentence",
                json=payload.model_dump(),
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("AI /sentence 호출 실패, fallback 문장을 반환합니다: %s", exc)
        return _fallback_sentence(payload, f"fallback: {exc}")


async def fetch_report_insight(stats: dict) -> Optional[str]:
    """리포트 통계 → GPT 자연어 해석. 실패하면 None(규칙기반 유지)."""
    if settings.use_mock_ai:
        return None
    try:
        async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
            r = await client.post(f"{settings.ai_server_url}/report/insight", json={"stats": stats})
            r.raise_for_status()
            return r.json().get("insight")
    except Exception as exc:
        logger.warning("AI /report/insight 호출 실패: %s", exc)
        return None


async def fetch_emotion_diary(payload: dict) -> Optional[dict]:
    """그날 사용 기록 → 감정일기 {mood, diary}. 실패하면 None."""
    if settings.use_mock_ai:
        return None
    try:
        async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
            r = await client.post(f"{settings.ai_server_url}/emotion-diary", json=payload)
            r.raise_for_status()
            return r.json()
    except Exception as exc:
        logger.warning("AI /emotion-diary 호출 실패: %s", exc)
        return None


async def fetch_card_image(text: str, baby_id: int) -> Optional[str]:
    """단어카드 개인화 이미지(아이별 캐릭터가 그 단어를 보여줌). AI /image kind=word.
    실패하면 None(카드는 이미지 없이 생성)."""
    if settings.use_mock_ai:
        return None
    try:
        async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
            response = await client.post(
                f"{settings.ai_server_url}/image",
                json={"sentence": text, "baby_id": baby_id, "kind": "word"},
            )
            response.raise_for_status()
            return response.json().get("image_url")
    except Exception as exc:
        logger.warning("AI /image(단어카드) 호출 실패: %s", exc)
        return None


async def fetch_related_words(text: str, count: int, exclude: list[str]) -> list[dict]:
    """
    부모 단어추가용 관련 단어(DB 에 없는 새 단어) 후보. AI 서버 /related-words 프록시.
    GPT 키가 없거나 실패하면 빈 목록(생성형이라 fallback 으론 새 단어 생성 불가).
    """
    if settings.use_mock_ai:
        return []

    try:
        async with httpx.AsyncClient(timeout=_AI_TIMEOUT) as client:
            response = await client.post(
                f"{settings.ai_server_url}/related-words",
                json={"text": text, "count": count, "exclude": exclude},
            )
            response.raise_for_status()
            return response.json().get("related_words", [])
    except Exception as exc:
        logger.warning("AI /related-words 호출 실패: %s", exc)
        return []
