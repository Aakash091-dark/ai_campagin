# app/config/settings.py

import os

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):

    # =========================================================
    # APP
    # =========================================================
    APP_NAME: str = "Lemon AI Engine"
    APP_VERSION: str = "1.0.0"

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # =========================================================
    # API
    # =========================================================
    API_V1_PREFIX: str = "/api/v1"

    # =========================================================
    # SECURITY
    # =========================================================
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "super-secret-key"
    )

    JWT_ALGORITHM: str = os.getenv(
        "JWT_ALGORITHM",
        "HS256"
    )

    # =========================================================
    # AI MODELS
    # =========================================================
    AI_MODEL: str = os.getenv(
        "AI_MODEL",
        "claude-sonnet-4-20250514"
    )

    AI_MAX_TOKENS: int = int(
        os.getenv("AI_MAX_TOKENS", "2048")
    )

    AI_TEMPERATURE: float = float(
        os.getenv("AI_TEMPERATURE", "0.1")
    )

    ANTHROPIC_API_KEY: str = os.getenv(
        "ANTHROPIC_API_KEY",
        ""
    )

    OPENAI_API_KEY: str = os.getenv(
        "OPENAI_API_KEY",
        ""
    )

    # =========================================================
    # CONCURRENCY GUARDS
    # =========================================================
    MAX_CONCURRENT_AGENTS: int = int(
        os.getenv("AI_MAX_CONCURRENT", "10")
    )

    MAX_PER_USER_CONCURRENT: int = int(
        os.getenv("AI_MAX_PER_USER", "2")
    )

    # =========================================================
    # EMBEDDINGS
    # =========================================================
    AI_EMBEDDING_MODEL: str = os.getenv(
        "AI_EMBEDDING_MODEL",
        "all-MiniLM-L6-v2"
    )

    EMBEDDING_DIMS: int = 384

    SIMILARITY_THRESHOLD: float = float(
        os.getenv("SIMILARITY_THRESHOLD", "0.70")
    )

    MAX_EMBED_CHARS: int = int(
        os.getenv("MAX_EMBED_CHARS", "8000")
    )

    # =========================================================
    # POSTGRES
    # =========================================================
    POSTGRES_DIRECT_HOST: str = os.getenv(
        "POSTGRES_DIRECT_HOST",
        "192.168.65.2"
    )

    POSTGRES_PORT: str = os.getenv(
        "POSTGRES_PORT",
        "5432"
    )

    POSTGRES_USER: str = os.getenv(
        "POSTGRES_USER",
        "postgres"
    )

    POSTGRES_PASSWORD: str = os.getenv(
        "POSTGRES_PASSWORD",
        "admin"
    )

    POSTGRES_DB: str = os.getenv(
        "POSTGRES_DB",
        "lemonmaxx_db"
    )

    DATABASE_URL: str = ""

    # =========================================================
    # REDIS
    # =========================================================
    REDIS_URL: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )

    # =========================================================
    # BACKEND API
    # =========================================================
    BACKEND_BASE_URL: str = os.getenv(
        "BACKEND_BASE_URL",
        "http://localhost:8001"
    )

    BACKEND_API_KEY: str = os.getenv(
        "BACKEND_API_KEY",
        ""
    )

    AUTH_TOKEN: str = os.getenv(
        "AUTH_TOKEN",
        ""
    )

    # =========================================================
    # CELERY
    # =========================================================
    CELERY_BROKER_URL: str = os.getenv(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/1"
    )

    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/2"
    )

    # =========================================================
    # LOGGING
    # =========================================================
    LOG_LEVEL: str = os.getenv(
        "LOG_LEVEL",
        "INFO"
    )

    # =========================================================
    # WEBSOCKETS
    # =========================================================
    WS_HEARTBEAT_INTERVAL: int = int(
        os.getenv("WS_HEARTBEAT_INTERVAL", "30")
    )

    # =========================================================
    # CORS
    # =========================================================
    ALLOWED_ORIGINS: list[str] = [
        "*"
    ]

    # =========================================================
    # BUILD DATABASE URL
    # =========================================================
    def build_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_DIRECT_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

settings.DATABASE_URL = settings.build_database_url()