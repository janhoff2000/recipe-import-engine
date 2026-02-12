"""API authentication."""

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
