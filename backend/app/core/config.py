from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "Crackstack API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: object) -> list[str]:
        if not v:
            return ["http://localhost:5173", "http://localhost:3000"]
        if isinstance(v, list):
            return v
        import json as _json
        try:
            parsed = _json.loads(str(v))
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return [s.strip() for s in str(v).split(",") if s.strip()]

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    RSA_PRIVATE_KEY_PATH: Optional[str] = None
    RSA_PUBLIC_KEY_PATH: Optional[str] = None
    SECRET_KEY: str = "change-me-in-production"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "crackstack"
    POSTGRES_PASSWORD: str = "crackstack"
    POSTGRES_DB: str = "crackstack"
    DATABASE_URL: Optional[str] = None

    REDIS_URL: Optional[str] = None
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    SENTRY_DSN: Optional[str] = None

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    FRONTEND_URL: str = "http://localhost:5173"

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_MAX_TOKENS: int = 4096
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int = 4096
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    AWS_REGION: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL.replace("+asyncpg", "")
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        if self.UPSTASH_REDIS_REST_URL and self.UPSTASH_REDIS_REST_TOKEN:
            host = self.UPSTASH_REDIS_REST_URL.replace("https://", "").replace("http://", "")
            return f"rediss://default:{self.UPSTASH_REDIS_REST_TOKEN}@{host}:6379"
        if self.REDIS_URL:
            return self.REDIS_URL
        return "redis://localhost:6379/0"


settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
