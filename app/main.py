from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import Base, engine
from app.routers import cards, children, expressions, health, logs, recommendations


Base.metadata.create_all(bind=engine)

TAGS_METADATA = [
    {"name": "health", "description": "서버 헬스 체크"},
    {"name": "children", "description": "아동 기본 정보 조회"},
    {"name": "cards", "description": "카드 목록 조회 + 부모 단어추가용 관련 단어 추천"},
    {"name": "recommendations", "description": "다음 단어 추천 (AI 서버 프록시)"},
    {"name": "expressions", "description": "‘말하기’ 멀티모달 문장 생성·저장 (AI 서버 프록시)"},
    {"name": "logs", "description": "단어 사용 로그 적재"},
]

app = FastAPI(
    title=settings.app_name,
    description=(
        "소리싹 백엔드 API. 프론트(React Native)가 `"
        + settings.api_prefix
        + "` 로 호출하는 메인 서버다.\n\n"
        "추천·멀티모달(문장/이미지/음성)은 내부 AI 서버(sorisak-ai, FastAPI :8001)를 "
        "`httpx` 로 프록시한다. 모든 응답은 `{ success, data, message }` 래퍼로 감싸며, "
        "`data` 의 구조는 각 엔드포인트 스키마를 참고한다."
    ),
    version="2.0.0",
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(children.router, prefix=settings.api_prefix)
app.include_router(cards.router, prefix=settings.api_prefix)
app.include_router(recommendations.router, prefix=settings.api_prefix)
app.include_router(expressions.router, prefix=settings.api_prefix)
app.include_router(logs.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs"}
