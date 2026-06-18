from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


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

    # 인증 (JWT)
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-insecure-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 기본 7일

    # 카카오 로그인 (나중에 키 발급 후 채움)
    kakao_rest_api_key: str = os.getenv("KAKAO_REST_API_KEY", "")


settings = Settings()
