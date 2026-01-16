"""API authentication utilities."""

from fastapi import Header, HTTPException, status

from recipe_importer.config import get_settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-Api-Key")) -> str:
    """Verify the service API key from request header."""
    settings = get_settings()

    if not settings.api_key:
        # No API key configured = open access (dev mode)
        return x_api_key

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return x_api_key


def get_llm_api_key(
    provider: str,
    byok_key: str | None = None,
) -> str:
    """Get LLM API key - prefer BYOK, fall back to service defaults."""
    if byok_key:
        return byok_key

    settings = get_settings()

    provider_keys = {
        "openai": settings.openai_api_key,
        "gemini": settings.google_api_key,
        "anthropic": settings.anthropic_api_key,
    }

    key = provider_keys.get(provider.lower())
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No API key available for provider '{provider}'. "
            "Provide X-LLM-Api-Key header or configure server defaults.",
        )

    return key
