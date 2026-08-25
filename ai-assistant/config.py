from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)
from pydantic import Field  # Додаємо імпорт Field


class Settings(BaseSettings):
    # We say this is a string, but by default Pydantic will find it in .env itself
    gemini_api_key: str = Field(default=None)
    drf_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
