"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field


class Settings(BaseModel):
    """Runtime configuration for the FinAI Risk Platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    app_name: str = Field(default="FinAI Risk Platform")
    app_env: str = Field(default="dev")
    model_path: str = Field(default="artifacts/risk_model.joblib")
    model_encoder_path: str = Field(default="artifacts/risk_label_encoder.joblib")


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object for the current process."""

    return Settings(
        app_name=os.getenv("APP_NAME", "FinAI Risk Platform"),
        app_env=os.getenv("APP_ENV", "dev"),
        model_path=os.getenv("MODEL_PATH", "artifacts/risk_model.joblib"),
        model_encoder_path=os.getenv(
            "MODEL_ENCODER_PATH",
            "artifacts/risk_label_encoder.joblib",
        ),
    )
