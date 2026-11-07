from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AYUVAN Backend"
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./ayuvan.db"
    redis_url: str | None = None
    use_arq: bool = False

    whatsapp_phone_number_id: str | None = None
    whatsapp_business_account_id: str | None = None
    whatsapp_access_token: SecretStr | None = None
    meta_app_secret: SecretStr | None = None
    webhook_verify_token: SecretStr | None = None
    graph_api_version: str = "v22.0"
    whatsapp_test_recipient: str | None = None
    # Optional Meta WhatsApp Flow. A Flow must be created and published in Meta before
    # setting this value; standard interactive questions remain the safe fallback.
    whatsapp_symptom_intake_flow_id: str | None = None
    whatsapp_symptom_intake_flow_screen: str = "SYMPTOM_INTAKE"

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.1-flash-lite"
    allow_test_user_auto_provision: bool = False
    test_user_phone: str | None = None

    @field_validator("database_url")
    @classmethod
    def normalise_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
