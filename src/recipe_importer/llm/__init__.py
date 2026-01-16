"""LLM provider exports and factory."""

from typing import Optional

from recipe_importer.llm.anthropic import AnthropicProvider
from recipe_importer.llm.base import LLMProvider
from recipe_importer.llm.gemini import GeminiProvider
from recipe_importer.llm.openai import OpenAIProvider

__all__ = [
    "LLMProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "AnthropicProvider",
    "get_provider",
]

PROVIDERS = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
}


def get_provider(
    provider_name: str, api_key: str, model: Optional[str] = None
) -> LLMProvider:
    """Factory function to get an LLM provider by name."""
    provider_class = PROVIDERS.get(provider_name.lower())
    if not provider_class:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider: {provider_name}. Available: {available}")
    return provider_class(api_key=api_key, model=model)
