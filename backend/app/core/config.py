"""
Application configuration.

All settings are loaded from environment variables (or a .env file in dev).
For production, set these via your deployment platform's secret manager —
never commit real secrets to source control.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "TrustWipe API"
    ENVIRONMENT: str = "development"  # development | production

    # Database. Defaults to local SQLite for zero-setup dev; swap to
    # postgresql+asyncpg://user:pass@host:5432/dbname for production.
    DATABASE_URL: str = "sqlite+aiosqlite:///./trustwipe.db"

    # JWT auth (used from Phase 5 onward, defined now so config is stable)
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-real-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ECDSA signing keys (PEM strings). In production these should be
    # injected via a secrets manager (AWS Secrets Manager, Vault, etc.),
    # never stored in the repo. If unset, Phase 1 code generates an
    # ephemeral dev keypair at startup — fine for local testing, NOT for prod.
    SIGNING_PRIVATE_KEY_PEM: str | None = None
    SIGNING_PUBLIC_KEY_PEM: str | None = None

    # Public base URL used to build QR-code verification links
    PUBLIC_BASE_URL: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
