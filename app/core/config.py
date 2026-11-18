from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, читаются из .env / переменных окружения."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenRouter
    openrouter_api_key: str = ""
    model_name: str = "stealth/space-bunny-alpha"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_timeout: int = 60

    # Сервер
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
