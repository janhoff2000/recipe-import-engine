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
from recipe_importer.config import get_settings
from recipe_importer.core.exceptions import (
    ExtractionError,
    FetchError,
    NoRecipeFoundError,
    PlatformNotSupportedError,
)
from recipe_importer.core.pipeline import create_pipeline

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
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def import_recipe(
    request: ImportRequest,
    _api_key: str = Depends(verify_api_key),
    x_llm_api_key: str | None = Header(None, alias="X-LLM-Api-Key"),
    x_meta_app_token: str | None = Header(None, alias="X-Meta-App-Token"),
) -> ImportResponse:
    """Import a recipe from a URL.

    - **url**: The URL to import from (currently supports Instagram)
    - **provider**: LLM provider to use (openai, gemini, anthropic)
    - **model**: Specific model override (optional)
    - **skip_recipe_check**: Skip heuristic recipe detection (optional)

    Headers:
    - **X-Api-Key**: Service API key (required)
    - **X-LLM-Api-Key**: Your own LLM API key (BYOK, optional)
    - **X-Meta-App-Token**: Your own Meta App Token (BYOK, optional)
    """
    settings = get_settings()

    try:
        llm_api_key = get_llm_api_key(request.provider, x_llm_api_key)

        meta_token = x_meta_app_token or settings.effective_meta_token

        pipeline = create_pipeline(
            provider_name=request.provider,
            llm_api_key=llm_api_key,
            model=request.model,
            meta_app_token=meta_token,
        )

        result = await pipeline.import_from_url(
            str(request.url),
            skip_recipe_check=request.skip_recipe_check,
        )

        return ImportResponse(
            recipe=result.recipe,
            extraction_method=result.extraction_method,
            provider_used=result.provider_used,
            model_used=result.model_used,
        )

    except PlatformNotSupportedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except NoRecipeFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except FetchError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except ExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {e!s}",
        ) from e
