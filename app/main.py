from fastapi import FastAPI

from app.core.config import settings
from app.db import Base, engine
from app.routers import cards, children, expressions, health, logs, recommendations


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(children.router, prefix=settings.api_prefix)
app.include_router(cards.router, prefix=settings.api_prefix)
app.include_router(recommendations.router, prefix=settings.api_prefix)
app.include_router(expressions.router, prefix=settings.api_prefix)
app.include_router(logs.router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs"}
