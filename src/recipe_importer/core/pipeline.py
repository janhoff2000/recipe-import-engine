"""Recipe import pipeline orchestrator."""

import logging

import httpx

from recipe_importer.config import get_settings
from recipe_importer.core.exceptions import (
    ExtractionError,
    NoRecipeFoundError,
    PlatformNotSupportedError,
)
from recipe_importer.core.models import ExtractionResult, RecipeDTO
from recipe_importer.fetchers.base import Fetcher, FetchResult
from recipe_importer.fetchers.instagram import InstagramFetcher
from recipe_importer.llm import get_provider
from recipe_importer.llm.base import ExtractionOutput, LLMProvider
from recipe_importer.parsers.caption import looks_like_recipe, prepare_for_extraction
from recipe_importer.tracking.tracker import Tracker

logger = logging.getLogger(__name__)


class RecipeImportPipeline:
    """Orchestrates the recipe import process.

    Flow: URL -> Fetcher -> Parser -> LLM -> RecipeDTO
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        meta_app_token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        tracker: Tracker | None = None,
    ) -> None:
        self.llm = llm_provider
        self._tracker = tracker
        self._fetchers: list[Fetcher] = [
            InstagramFetcher(
                meta_app_token=meta_app_token,
                http_client=http_client,
            ),
        ]

    def get_fetcher(self, url: str) -> Fetcher:
        """Find a fetcher that can handle the given URL."""
        for fetcher in self._fetchers:
            if fetcher.can_handle(url):
                return fetcher
        raise PlatformNotSupportedError(f"No fetcher available for URL: {url}")

    async def import_from_url(
        self,
        url: str,
        *,
        skip_recipe_check: bool = False,
    ) -> ExtractionResult:
        """Import a recipe from a URL."""
        logger.info("Starting import from URL: %s", url)

        fetcher = self.get_fetcher(url)
        content = await fetcher.fetch(url)

        return await self._extract_from_content(
            content,
            skip_recipe_check=skip_recipe_check,
        )

    async def _extract_from_content(
        self,
        content: FetchResult,
        *,
        skip_recipe_check: bool = False,
    ) -> ExtractionResult:
        """Extract recipe from fetched content."""
        if not content.caption:
            raise NoRecipeFoundError("No caption/text content available to extract from")

        if not skip_recipe_check and not looks_like_recipe(content.caption):
            raise NoRecipeFoundError(
                "Caption doesn't appear to contain a recipe. "
                "Use skip_recipe_check=True to force extraction."
            )

        prepared_text = prepare_for_extraction(content.caption)
        output, retry_count = await self._extract_with_retry(prepared_text)

        output.recipe.source_url = content.url

        # Track the extraction
        if self._tracker:
            await self._tracker.record_extraction(
                url=content.url,
                platform=content.platform,
                model=self.llm.model,
                provider=self.llm.name,
                output=output,
                retry_count=retry_count,
            )

        return ExtractionResult(
            recipe=output.recipe,
            extraction_method="llm",
            provider_used=self.llm.name,
            model_used=self.llm.model,
        )

    async def _extract_with_retry(
        self,
        text: str,
        max_retries: int = 2,
    ) -> tuple[ExtractionOutput, int]:
        """Extract recipe with retry logic. Returns (output, retry_count)."""
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                output = await self.llm.extract_recipe(text)

                if self._validate_recipe(output.recipe):
                    logger.info("Extraction succeeded on attempt %d", attempt + 1)
                    return output, attempt

                last_error = ExtractionError(
                    f"Extracted recipe missing required fields (attempt {attempt + 1})"
                )

            except ExtractionError:
                raise

            except Exception as e:
                last_error = e
                logger.warning("Extraction attempt %d failed: %s", attempt + 1, e)

                # Track failure on final attempt
                if attempt == max_retries and self._tracker:
                    error_type = "timeout" if "timeout" in str(e).lower() else "api_error"
                    await self._tracker.record_failure(
                        url="",
                        platform="unknown",
                        model=self.llm.model,
                        provider=self.llm.name,
                        error_type=error_type,
                        retry_count=attempt,
                    )
                if attempt == max_retries:
                    break

        raise ExtractionError(
            f"Failed to extract valid recipe after {max_retries + 1} attempts"
        ) from last_error

    def _validate_recipe(self, recipe: RecipeDTO) -> bool:
        """Validate that extracted recipe has required fields."""
        if not recipe.title or not recipe.title.strip():
            return False
        if not recipe.ingredients:
            return False
        return True


def create_pipeline(
    model: str,
    *,
    meta_app_token: str | None = None,
    http_client: httpx.AsyncClient | None = None,
    tracker: Tracker | None = None,
) -> RecipeImportPipeline:
    """Factory function to create a configured pipeline."""
    settings = get_settings()

    # Get API key for the provider
    if model.startswith("gpt-"):
        api_key = settings.openai_api_key or ""
    elif model.startswith("gemini-"):
        api_key = settings.google_api_key or ""
    else:
        api_key = ""

    llm_provider = get_provider(model, api_key)
    return RecipeImportPipeline(
        llm_provider,
        meta_app_token=meta_app_token,
        http_client=http_client,
        tracker=tracker,
    )
