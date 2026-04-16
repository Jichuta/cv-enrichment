"""Application settings — loaded from .env via pydantic-settings."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_NAME: str = "CV Enrichment API"
    APP_VERSION: str = "1.0.0"

    # ── Security ──────────────────────────────────────────────────────────────
    API_SECRET_KEY: str = "dev-secret-key"
    CORS_ORIGINS: list[str] = ["*"]

    # ── Databricks ────────────────────────────────────────────────────────────
    DATABRICKS_HOST: str = "https://dbc-ee3269b0-d8c2.cloud.databricks.com"
    DATABRICKS_TOKEN: str = ""

    # ── Databricks Jobs ───────────────────────────────────────────────────────
    DATABRICKS_ENRICHMENT_JOB_ID: int = 884092477536605
    DATABRICKS_JOB_POLL_INTERVAL_SECS: int = 5
    DATABRICKS_JOB_TIMEOUT_SECS: int = 300

    # ── Databricks LLM (direct model serving) ─────────────────────────────────
    DATABRICKS_LLM_MODEL: str = "databricks-gemma-3-12b"
    DATABRICKS_LLM_MAX_TOKENS: int = 5000
    DATABRICKS_LLM_TEMPERATURE: float = 0.0

    @field_validator("DATABRICKS_HOST")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def databricks_auth_header(self) -> str:
        return f"Bearer {self.DATABRICKS_TOKEN}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
