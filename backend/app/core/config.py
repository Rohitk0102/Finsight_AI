from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
from pathlib import Path
from typing import List, Union
import json


CORE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CORE_DIR.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
BACKEND_ENV_FILE = str(BACKEND_DIR / ".env")
PROJECT_ENV_FILE = str(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Order matters: later files override earlier ones.
        # Load project root first, then backend/.env so local backend values win.
        env_file=(PROJECT_ENV_FILE, BACKEND_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "Finsight AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # API
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "https://localhost:3000"]
    FRONTEND_APP_URL: str = "https://localhost:3000"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from JSON array or comma-separated string."""
        if isinstance(v, str):
            raw = v.strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass

            if "," in raw:
                return [item.strip().strip('"').strip("'") for item in raw.split(",") if item.strip()]
            return [raw.strip('"').strip("'")]
        return v

    # Supabase (database only — auth is handled by Clerk)
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # Clerk
    CLERK_JWKS_URL: str  # e.g. https://<clerk-frontend-api>/.well-known/jwks.json

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # External APIs
    ALPHA_VANTAGE_API_KEY: str = ""
    POLYGON_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    FMP_API_KEY: str = ""  # Financial Modeling Prep
    GNEWS_API_KEY: str = ""
    MARKETAUX_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    HUGGINGFACE_MARKETS_MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    FEATURE_MARKETS: bool = True

    # Broker OAuth
    ZERODHA_API_KEY: str = ""
    ZERODHA_API_SECRET: str = ""
    UPSTOX_CLIENT_ID: str = ""
    UPSTOX_CLIENT_SECRET: str = ""
    UPSTOX_REDIRECT_URI: str = "https://localhost:8000/api/v1/broker/upstox/callback"
    ANGEL_ONE_API_KEY: str = ""
    ANGEL_ONE_CLIENT_ID: str = ""

    # Encryption key for storing broker tokens in DB (32 bytes base64)
    BROKER_TOKEN_ENCRYPTION_KEY: str

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Rate limiting (requests per minute per IP)
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("Supabase configuration is required")

    if not settings.CLERK_JWKS_URL:
        raise ValueError("CLERK_JWKS_URL is required")

    if not settings.BROKER_TOKEN_ENCRYPTION_KEY:
        raise ValueError("BROKER_TOKEN_ENCRYPTION_KEY is required")

    try:
        import base64
        key_bytes = base64.urlsafe_b64decode(settings.BROKER_TOKEN_ENCRYPTION_KEY.encode())
        if len(key_bytes) != 32:
            raise ValueError("BROKER_TOKEN_ENCRYPTION_KEY must be 32 bytes base64-encoded")
    except Exception:
        raise ValueError("BROKER_TOKEN_ENCRYPTION_KEY must be valid base64-encoded 32-byte key")

    return settings


settings = get_settings()
