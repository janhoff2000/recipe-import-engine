"""Recipe import pipeline orchestrator."""

from recipe_importer.core.exceptions import (
    ExtractionError,
    NoRecipeFoundError,
    PlatformNotSupportedError,
)
from recipe_importer.core.models import ExtractionResult, RecipeDTO
from recipe_importer.fetchers.base import Fetcher, FetchResult
from recipe_importer.fetchers.instagram import InstagramFetcher
from recipe_importer.llm import LLMProvider, get_provider
from recipe_importer.parsers.caption import looks_like_recipe, prepare_for_extraction


class RecipeImportPipeline:
    """Orchestrates the recipe import process.

    Flow: URL → Fetcher → Parser → LLM → RecipeDTO
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        meta_app_token: str | None = None,
    ) -> None:
        """Initialize pipeline with LLM provider and optional Meta token."""
        self.llm = llm_provider
        self._fetchers: list[Fetcher] = [
            InstagramFetcher(meta_app_token=meta_app_token),
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
        """Import a recipe from a URL.

        Args:
            url: The URL to import from (Instagram, etc.)
            skip_recipe_check: If True, skip the heuristic recipe detection
                and always attempt LLM extraction.

        Returns:
            ExtractionResult with the extracted recipe and metadata.

        Raises:
            PlatformNotSupportedError: URL platform not supported
            FetchError: Failed to fetch content
            NoRecipeFoundError: Content doesn't appear to contain a recipe
            ExtractionError: LLM extraction failed
        """
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
        recipe = await self._extract_with_retry(prepared_text)

        recipe.source_url = content.url

        return ExtractionResult(
            recipe=recipe,
            extraction_method="llm",
            provider_used=self.llm.name,
            model_used=self.llm.model,
        )

    async def _extract_with_retry(
        self,
        text: str,
        max_retries: int = 2,
    ) -> RecipeDTO:
        """Extract recipe with retry logic for validation failures."""
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                recipe = await self.llm.extract_recipe(text)

                if self._validate_recipe(recipe):
                    return recipe

                last_error = ExtractionError(
                    f"Extracted recipe missing required fields (attempt {attempt + 1})"
                )

            except Exception as e:
                last_error = e
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
    provider_name: str,
    llm_api_key: str,
    *,
    model: str | None = None,
    meta_app_token: str | None = None,
) -> RecipeImportPipeline:
    """Factory function to create a configured pipeline."""
    llm_provider = get_provider(provider_name, llm_api_key, model)
    return RecipeImportPipeline(llm_provider, meta_app_token=meta_app_token)
