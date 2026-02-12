"""Tests for LLM provider extraction logic."""

import pytest

from recipe_importer.llm import get_provider
from recipe_importer.llm.base import ExtractionOutput
from recipe_importer.llm.gemini import GeminiProvider
from recipe_importer.llm.openai import OpenAIProvider


class TestGetProvider:
    """Test provider factory."""

    def test_openai_from_model_name(self):
        provider = get_provider("gpt-4.1-nano", "test-key")
        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "gpt-4.1-nano"
        assert provider.name == "openai"

    def test_gemini_from_model_name(self):
        provider = get_provider("gemini-2.5-flash-lite", "test-key")
        assert isinstance(provider, GeminiProvider)
        assert provider.model == "gemini-2.5-flash-lite"
        assert provider.name == "gemini"

    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            get_provider("claude-3-haiku", "test-key")

    def test_openai_different_models(self):
        for model in ["gpt-4.1-nano", "gpt-5-nano", "gpt-5-mini"]:
            provider = get_provider(model, "test-key")
            assert isinstance(provider, OpenAIProvider)
            assert provider.model == model


class TestOpenAIProvider:
    """Test OpenAI provider."""

    def test_initialization(self):
        provider = OpenAIProvider(api_key="test-key", model="gpt-5-nano")
        assert provider.name == "openai"
        assert provider.model == "gpt-5-nano"

    def test_default_model(self):
        provider = OpenAIProvider(api_key="test-key")
        assert provider.model == "gpt-4.1-nano"


class TestGeminiProvider:
    """Test Gemini provider."""

    def test_initialization(self):
        provider = GeminiProvider(api_key="test-key", model="gemini-2.5-flash-lite")
        assert provider.name == "gemini"
        assert provider.model == "gemini-2.5-flash-lite"

    def test_default_model(self):
        provider = GeminiProvider(api_key="test-key")
        assert provider.model == "gemini-2.5-flash-lite"


class TestExtractionOutput:
    """Test ExtractionOutput dataclass."""

    def test_creation(self, sample_recipe_dto):
        output = ExtractionOutput(
            recipe=sample_recipe_dto,
            input_tokens=500,
            output_tokens=300,
            latency_ms=1200,
        )
        assert output.input_tokens == 500
        assert output.output_tokens == 300
        assert output.latency_ms == 1200
        assert output.recipe.title == "Chocolate Chip Cookies"
