"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional

from recipe_importer.core.models import RecipeDTO


class LLMProvider(ABC):
    """Base class for LLM provider adapters."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        """Initialize the provider with API key and optional model override."""
        self.api_key = api_key
        self.model = model or self.default_model

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'openai', 'gemini', 'anthropic')."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model to use if none specified."""
        ...

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """List of supported model identifiers."""
        ...

    @abstractmethod
    async def extract_recipe(
        self, text: str, image_url: Optional[str] = None
    ) -> RecipeDTO:
        """Extract recipe from text (and optionally an image)."""
        ...

    def _get_extraction_prompt(self) -> str:
        """Get the system prompt for recipe extraction."""
        return """You are a recipe extraction assistant. Extract the recipe from the provided text.

Return a JSON object with these fields:
- title: string (recipe name)
- servings: number or null (number of servings)
- duration_minutes: number or null (total time in minutes)
- ingredients: array of objects with {name, quantity, unit, note}
  - name: string (ingredient name)
  - quantity: number or null
  - unit: string or null (e.g., "cups", "g", "tbsp")
  - note: string or null (e.g., "chopped", "room temperature")
- steps: array of strings (cooking instructions in order)

Be precise with quantities. Convert fractions to decimals (½ = 0.5).
If information is missing, use null.
Return ONLY valid JSON, no markdown or explanation."""
