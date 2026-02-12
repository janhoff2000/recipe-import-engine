"""LLM provider exports and factory."""

from recipe_importer.llm.base import ExtractionOutput, LLMProvider
from recipe_importer.llm.gemini import GeminiProvider
from recipe_importer.llm.openai import OpenAIProvider

__all__ = [
    "ExtractionOutput",
    "GeminiProvider",
    "LLMProvider",
    "OpenAIProvider",
    "get_provider",
]


def get_provider(model: str, api_key: str) -> OpenAIProvider | GeminiProvider:
    """Create an LLM provider based on model name.

    Auto-detects provider from model prefix:
    - gpt-* → OpenAI
    - gemini-* → Gemini
    """
    if model.startswith("gpt-"):
        return OpenAIProvider(api_key=api_key, model=model)
    if model.startswith("gemini-"):
        return GeminiProvider(api_key=api_key, model=model)
    raise ValueError(f"Unknown model: {model}. Model must start with 'gpt-' or 'gemini-'.")
