"""Google Gemini LLM provider adapter."""

import json
from typing import Any, override

from recipe_importer.core.models import RecipeDTO
from recipe_importer.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini provider for recipe extraction."""

    @property
    @override
    def name(self) -> str:
        return "gemini"

    @property
    @override
    def default_model(self) -> str:
        return "gemini-2.0-flash"  # Fast and cost-effective

    @property
    @override
    def supported_models(self) -> list[str]:
        return ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

    @override
    async def extract_recipe(self, text: str, image_url: str | None = None) -> RecipeDTO:
        """Extract recipe using Google Gemini."""
        # Import here to avoid module-level issues with google.generativeai
        import google.generativeai as genai  # pyright: ignore[reportPrivateImportUsage]

        genai.configure(api_key=self.api_key)  # pyright: ignore[reportUnknownMemberType]
        model = genai.GenerativeModel(self.model)  # pyright: ignore[reportUnknownMemberType]

        prompt = f"""{self._get_extraction_prompt()}

Text to extract from:
{text}"""

        # Note: For production, handle image_url by fetching and including as Part
        response = await model.generate_content_async(  # pyright: ignore[reportUnknownMemberType]
            prompt,
            generation_config=genai.GenerationConfig(  # pyright: ignore[reportUnknownMemberType]
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        content: str | None = response.text
        if not content:
            raise ValueError("Empty response from Gemini")

        data: dict[str, Any] = json.loads(content)
        return RecipeDTO.model_validate(data)
