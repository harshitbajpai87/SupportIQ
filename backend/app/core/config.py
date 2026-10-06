"""
SupportIQ — Application configuration
All settings are read from environment variables (or a .env file).
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "SupportIQ"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "dev-secret-key-please-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./supportiq.db"

    # ML
    CONFIDENCE_THRESHOLD: float = 0.35
    MODEL_VERSION: str = "1.0"

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"

    # Admin bootstrap (optional)
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""
    ADMIN_SECRET_KEY: str = "dev-admin-secret"


settings = Settings()
