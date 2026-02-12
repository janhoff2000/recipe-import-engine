"""OpenAI LLM provider adapter with structured output."""

import time

from openai import AsyncOpenAI

from recipe_importer.core.models import RecipeDTO
from recipe_importer.llm.base import EXTRACTION_PROMPT, ExtractionOutput


class OpenAIProvider:
    """OpenAI provider for recipe extraction using structured output."""

    name: str = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4.1-nano") -> None:
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key, timeout=30.0)

    async def extract_recipe(self, text: str) -> ExtractionOutput:
        """Extract recipe using OpenAI structured output."""
        start = time.monotonic()

        response = await self._client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": text},
            ],
            response_format=RecipeDTO,
            temperature=0.1,
        )

        latency_ms = int((time.monotonic() - start) * 1000)

        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI returned no parsed output")

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return ExtractionOutput(
            recipe=parsed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
