import httpx

from app.core.config import settings
from app.schemas import RecommendedWord, RecommendationRequest, RecommendationResult


async def fetch_recommendations(payload: RecommendationRequest) -> RecommendationResult:
    if settings.use_mock_ai:
        return RecommendationResult(
            baby_id=payload.baby_id,
            selected_word="mock-selected-word",
            recommended_words=[
                RecommendedWord(baby_card_id=None, card_id=1, text="주세요", pos="verb", system_score=0.95),
                RecommendedWord(baby_card_id=None, card_id=2, text="먹고 싶어요", pos="verb", system_score=0.91),
                RecommendedWord(baby_card_id=None, card_id=3, text="맛있어요", pos="adjective", system_score=0.88),
            ],
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.ai_server_url}/recommend",
            json=payload.model_dump(),
        )
        response.raise_for_status()
        return RecommendationResult(**response.json())
