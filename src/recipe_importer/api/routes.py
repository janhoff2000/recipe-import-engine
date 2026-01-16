"""API routes for recipe import."""

from fastapi import APIRouter, Depends, Header, HTTPException, status

from recipe_importer import __version__
from recipe_importer.api.auth import get_llm_api_key, verify_api_key
from recipe_importer.api.schemas import (
    ErrorResponse,
    HealthResponse,
    ImportRequest,
    ImportResponse,
)
from recipe_importer.llm import get_provider

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__)


@router.post(
    "/v1/import",
    response_model=ImportResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def import_recipe(
    request: ImportRequest,
    _api_key: str = Depends(verify_api_key),
    x_llm_api_key: str | None = Header(None, alias="X-LLM-Api-Key"),
) -> ImportResponse:
    """Import a recipe from a URL.

    - **url**: The URL to import from (Instagram, TikTok, YouTube, blog)
    - **provider**: LLM provider to use (openai, gemini, anthropic)
    - **model**: Specific model override (optional)

    Headers:
    - **X-Api-Key**: Service API key (required)
    - **X-LLM-Api-Key**: Your own LLM API key (BYOK, optional)
    """
    try:
        # Get LLM API key (BYOK or service default)
        llm_api_key = get_llm_api_key(request.provider, x_llm_api_key)

        # Get the LLM provider
        provider = get_provider(request.provider, llm_api_key, request.model)

        # TODO: Implement fetchers to get content from URL
        # For now, we'll use a placeholder
        # In production: content = await fetch_content(str(request.url))
        placeholder_content = f"Recipe content from {request.url}"

        # Extract recipe using LLM
        recipe = await provider.extract_recipe(placeholder_content)

        return ImportResponse(
            recipe=recipe,
            extraction_method="llm",
            provider_used=provider.name,
            model_used=provider.model,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {e!s}",
        ) from e
