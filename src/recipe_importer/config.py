"""Configuration management using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Service settings
    app_name: str = "Recipe Import Engine"
    debug: bool = False

    # API authentication
    api_key: str = ""  # Service-level API key for authenticating clients

    # Default LLM settings (used when client doesn't provide BYOK)
    default_llm_provider: str = "openai"
    default_llm_model: str | None = None

    # Provider API keys (optional - for managed/default mode)
    openai_api_key: str | None = None
    google_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Rate limiting
    rate_limit_per_minute: int = 60

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
