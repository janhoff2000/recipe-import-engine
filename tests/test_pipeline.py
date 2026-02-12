"""Tests for the recipe import pipeline."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from recipe_importer.core.exceptions import (
    ExtractionError,
    NoRecipeFoundError,
    PlatformNotSupportedError,
)
from recipe_importer.core.models import IngredientDTO, RecipeDTO
from recipe_importer.core.pipeline import RecipeImportPipeline
from recipe_importer.fetchers.base import FetchResult
from recipe_importer.llm.base import ExtractionOutput


class TestPipeline:
    """Test RecipeImportPipeline."""

    async def test_import_happy_path(self, mock_llm_provider, tracker):
        pipeline = RecipeImportPipeline(
            llm_provider=mock_llm_provider,
            meta_app_token="test-token",
            tracker=tracker,
        )

        # Mock fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.can_handle.return_value = True
        mock_fetcher.fetch = AsyncMock(
            return_value=FetchResult(
                url="https://instagram.com/p/test123/",
                platform="instagram",
                caption="Recipe: 2 cups flour, 1 cup sugar. Instructions: 1. Mix. 2. Bake.",
            )
        )
        pipeline._fetchers = [mock_fetcher]

        result = await pipeline.import_from_url("https://instagram.com/p/test123/")

        assert result.recipe.title == "Chocolate Chip Cookies"
        assert result.provider_used == "openai"
        assert result.model_used == "gpt-4.1-nano"
        assert result.extraction_method == "llm"

    async def test_unsupported_url(self, mock_llm_provider):
        pipeline = RecipeImportPipeline(llm_provider=mock_llm_provider)
        pipeline._fetchers = []  # No fetchers

        with pytest.raises(PlatformNotSupportedError):
            await pipeline.import_from_url("https://tiktok.com/video/123")

    async def test_no_caption(self, mock_llm_provider):
        pipeline = RecipeImportPipeline(llm_provider=mock_llm_provider)

        mock_fetcher = MagicMock()
        mock_fetcher.can_handle.return_value = True
        mock_fetcher.fetch = AsyncMock(
            return_value=FetchResult(
                url="https://instagram.com/p/test/",
                platform="instagram",
                caption=None,
            )
        )
        pipeline._fetchers = [mock_fetcher]

        with pytest.raises(NoRecipeFoundError, match="No caption"):
            await pipeline.import_from_url("https://instagram.com/p/test/")

    async def test_not_a_recipe(self, mock_llm_provider):
        pipeline = RecipeImportPipeline(llm_provider=mock_llm_provider)

        mock_fetcher = MagicMock()
        mock_fetcher.can_handle.return_value = True
        mock_fetcher.fetch = AsyncMock(
            return_value=FetchResult(
                url="https://instagram.com/p/test/",
                platform="instagram",
                caption="Beautiful sunset at the beach!",
            )
        )
        pipeline._fetchers = [mock_fetcher]

        with pytest.raises(NoRecipeFoundError, match="doesn't appear"):
            await pipeline.import_from_url("https://instagram.com/p/test/")

    async def test_skip_recipe_check(self, mock_llm_provider):
        pipeline = RecipeImportPipeline(llm_provider=mock_llm_provider)

        mock_fetcher = MagicMock()
        mock_fetcher.can_handle.return_value = True
        mock_fetcher.fetch = AsyncMock(
            return_value=FetchResult(
                url="https://instagram.com/p/test/",
                platform="instagram",
                caption="This is not a recipe at all",
            )
        )
        pipeline._fetchers = [mock_fetcher]

        # Should not raise with skip_recipe_check=True
        result = await pipeline.import_from_url(
            "https://instagram.com/p/test/",
            skip_recipe_check=True,
        )
        assert result.recipe.title == "Chocolate Chip Cookies"

    async def test_retry_on_api_error(self):
        provider = MagicMock()
        provider.name = "openai"
        provider.model = "gpt-4.1-nano"

        good_output = ExtractionOutput(
            recipe=RecipeDTO(
                title="Test Recipe",
                ingredients=[IngredientDTO(name="flour", quantity=1.0, unit="cup")],
                steps=["Mix"],
            ),
            input_tokens=100,
            output_tokens=50,
            latency_ms=500,
        )
        provider.extract_recipe = AsyncMock(side_effect=[RuntimeError("API timeout"), good_output])

        pipeline = RecipeImportPipeline(llm_provider=provider)
        output, retry_count = await pipeline._extract_with_retry("test text")

        assert output.recipe.title == "Test Recipe"
        assert retry_count == 1

    async def test_all_retries_exhausted(self):
        provider = MagicMock()
        provider.name = "openai"
        provider.model = "gpt-4.1-nano"
        provider.extract_recipe = AsyncMock(side_effect=RuntimeError("Always fails"))

        pipeline = RecipeImportPipeline(llm_provider=provider)

        with pytest.raises(ExtractionError, match="Failed to extract"):
            await pipeline._extract_with_retry("test text")

    def test_validate_recipe_valid(self, mock_llm_provider, sample_recipe_dto):
        pipeline = RecipeImportPipeline(llm_provider=mock_llm_provider)
        assert pipeline._validate_recipe(sample_recipe_dto) is True

    def test_validate_recipe_no_title(self, mock_llm_provider):
        pipeline = RecipeImportPipeline(llm_provider=mock_llm_provider)
        recipe = RecipeDTO(
            title="",
            ingredients=[IngredientDTO(name="flour")],
        )
        assert pipeline._validate_recipe(recipe) is False

    def test_validate_recipe_no_ingredients(self, mock_llm_provider):
        pipeline = RecipeImportPipeline(llm_provider=mock_llm_provider)
        recipe = RecipeDTO(title="Test", ingredients=[])
        assert pipeline._validate_recipe(recipe) is False
