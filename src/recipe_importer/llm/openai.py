"""OpenAI LLM provider adapter."""

import json
from typing import Optional

from openai import AsyncOpenAI

from recipe_importer.core.models import RecipeDTO
from recipe_importer.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider for recipe extraction."""

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"  # Cost-effective default

    @property
    def supported_models(self) -> list[str]:
        return ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]

    async def extract_recipe(
        self, text: str, image_url: Optional[str] = None
    ) -> RecipeDTO:
        """Extract recipe using OpenAI's structured output."""
        client = AsyncOpenAI(api_key=self.api_key)

        messages: list[dict] = [
            {"role": "system", "content": self._get_extraction_prompt()},
        ]

        # Build user message with optional image
        if image_url:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            })
        else:
            messages.append({"role": "user", "content": text})

        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore
            response_format={"type": "json_object"},
            temperature=0.1,  # Low temperature for consistent extraction
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")

        data = json.loads(content)
        return RecipeDTO.model_validate(data)
