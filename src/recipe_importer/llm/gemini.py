"""Google Gemini LLM provider adapter with structured output."""

import time

from google import genai
from google.genai.types import GenerateContentConfig

from recipe_importer.core.models import RecipeDTO
from recipe_importer.llm.base import EXTRACTION_PROMPT, ExtractionOutput


class GeminiProvider:
    """Google Gemini provider for recipe extraction using structured output."""

    name: str = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite") -> None:
        self.model = model
        self._client = genai.Client(api_key=api_key)

    async def extract_recipe(self, text: str) -> ExtractionOutput:
        """Extract recipe using Gemini structured output."""
        start = time.monotonic()

        response = await self._client.aio.models.generate_content(  # pyright: ignore[reportUnknownMemberType]
            model=self.model,
            contents=f"{EXTRACTION_PROMPT}\n\nText to extract from:\n{text}",
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RecipeDTO,
                temperature=0.1,
            ),
        )

        latency_ms = int((time.monotonic() - start) * 1000)

        if not response.text:
            raise ValueError("Gemini returned empty response")

        recipe = RecipeDTO.model_validate_json(response.text)

        input_tokens = 0
        output_tokens = 0
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        return ExtractionOutput(
            recipe=recipe,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
