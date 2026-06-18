from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from app.core.config import settings
from app.db import Base, engine
from app.routers import (
    auth,
    cards,
    categories,
    children,
    expressions,
    health,
    logs,
    recommendations,
)


def _ensure_parent_id_column() -> None:
    """기존 baby_basic_information 에 parent_id 컬럼이 없으면 추가(간이 마이그레이션).

    create_all 은 새 테이블(parent)만 만들고 기존 테이블 컬럼은 추가하지 않으므로,
    이미 존재하는 RDS/sqlite 테이블에 parent_id 를 ALTER 로 보강한다.
    """
    inspector = inspect(engine)
    if "baby_basic_information" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("baby_basic_information")}
    if "parent_id" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE baby_basic_information ADD COLUMN parent_id INTEGER")
            )


Base.metadata.create_all(bind=engine)
_ensure_parent_id_column()

TAGS_METADATA = [
    {"name": "auth", "description": "회원가입 / 로그인 / 카카오 / 내 정보 — JWT 발급"},
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

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(children.router, prefix=settings.api_prefix)
app.include_router(cards.router, prefix=settings.api_prefix)
app.include_router(categories.router, prefix=settings.api_prefix)
app.include_router(recommendations.router, prefix=settings.api_prefix)
app.include_router(expressions.router, prefix=settings.api_prefix)
app.include_router(logs.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs"}
