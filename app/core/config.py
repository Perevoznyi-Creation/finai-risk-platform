"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    """Runtime configuration for the FinAI Risk Platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    app_name: str = Field(default="FinAI Risk Platform")
    app_env: str = Field(default="dev")
    database_url: str = Field(default="sqlite:///./finai.db")
    api_key_salt: str = Field(default="change-me-in-production")
    model_path: str = Field(default="artifacts/risk_model.joblib")
    model_encoder_path: str = Field(default="artifacts/risk_label_encoder.joblib")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object for the current process."""

    return Settings(
        app_name=os.getenv("APP_NAME", "FinAI Risk Platform"),
        app_env=os.getenv("APP_ENV", "dev"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./finai.db"),
        api_key_salt=os.getenv("API_KEY_SALT", "change-me-in-production"),
        model_path=os.getenv("MODEL_PATH", "artifacts/risk_model.joblib"),
        model_encoder_path=os.getenv(
            "MODEL_ENCODER_PATH",
            "artifacts/risk_label_encoder.joblib",
        ),
    )
