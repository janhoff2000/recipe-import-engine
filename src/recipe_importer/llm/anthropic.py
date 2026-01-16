"""Anthropic Claude LLM provider adapter."""

import json
from typing import Optional

from anthropic import AsyncAnthropic

from recipe_importer.core.models import RecipeDTO
from recipe_importer.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider for recipe extraction."""

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-3-haiku-20240307"  # Fast and cost-effective

    @property
    def supported_models(self) -> list[str]:
        return [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
        ]

    async def extract_recipe(
        self, text: str, image_url: Optional[str] = None
    ) -> RecipeDTO:
        """Extract recipe using Anthropic Claude."""
        client = AsyncAnthropic(api_key=self.api_key)

        content: list[dict] = [{"type": "text", "text": text}]

        # Add image if provided
        if image_url:
            # Note: For production, fetch image and convert to base64
            pass

        response = await client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self._get_extraction_prompt(),
            messages=[{"role": "user", "content": content}],
        )

        # Extract text from response
        response_text = ""
        for block in response.content:
            if block.type == "text":
                response_text = block.text
                break

        if not response_text:
            raise ValueError("Empty response from Anthropic")

        # Claude may wrap JSON in markdown, extract it
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())
        return RecipeDTO.model_validate(data)
