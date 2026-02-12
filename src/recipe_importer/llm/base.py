"""LLM provider protocol and extraction output."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from recipe_importer.core.models import RecipeDTO


@dataclass
class ExtractionOutput:
    """Output from an LLM extraction call."""

    recipe: RecipeDTO
    input_tokens: int
    output_tokens: int
    latency_ms: int


EXTRACTION_PROMPT = """\
You are a recipe extraction assistant. Extract the recipe from the provided text.

Extract these fields:
- title: string (recipe name)
- servings: number or null (number of servings)
- duration_minutes: number or null (total time in minutes)
- ingredients: array of objects with {name, quantity, unit, note}
  - name: string (ingredient name)
  - quantity: number or null
  - unit: string or null (e.g., "cups", "g", "tbsp")
  - note: string or null (e.g., "chopped", "room temperature")
- steps: array of strings (cooking instructions in order)

Be precise with quantities. Convert fractions to decimals (1/2 = 0.5).
If information is missing, use null."""


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM provider adapters."""

    name: str
    model: str

    async def extract_recipe(self, text: str) -> ExtractionOutput: ...
