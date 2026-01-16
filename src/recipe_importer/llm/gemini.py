"""Google Gemini LLM provider adapter."""

import json
from typing import Optional

import google.generativeai as genai

from recipe_importer.core.models import RecipeDTO
from recipe_importer.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini provider for recipe extraction."""

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return "gemini-2.0-flash"  # Fast and cost-effective

    @property
    def supported_models(self) -> list[str]:
        return ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

    async def extract_recipe(
        self, text: str, image_url: Optional[str] = None
    ) -> RecipeDTO:
        """Extract recipe using Google Gemini."""
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)

        prompt = f"""{self._get_extraction_prompt()}

Text to extract from:
{text}"""

        # Note: For production, handle image_url by fetching and including as Part
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        content = response.text
        if not content:
            raise ValueError("Empty response from Gemini")

        data = json.loads(content)
        return RecipeDTO.model_validate(data)
