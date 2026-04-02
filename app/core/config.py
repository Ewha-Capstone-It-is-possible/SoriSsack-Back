from dataclasses import dataclass
import os


def _as_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "SoriSsack Backend")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./sorissack.db")
    ai_server_url: str = os.getenv("AI_SERVER_URL", "http://127.0.0.1:8001")
    use_mock_ai: bool = _as_bool(os.getenv("USE_MOCK_AI"), True)


settings = Settings()
