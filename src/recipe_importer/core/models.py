"""Core domain models for recipe extraction."""

from typing import Optional
from pydantic import BaseModel, Field


class IngredientDTO(BaseModel):
    """Extracted ingredient data."""

    name: str = Field(..., description="Ingredient name")
    quantity: Optional[float] = Field(None, description="Numeric quantity")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    note: Optional[str] = Field(None, description="Additional notes (e.g., 'chopped')")


class RecipeDTO(BaseModel):
    """Extracted recipe data."""

    title: str = Field(..., description="Recipe title")
    servings: Optional[int] = Field(None, description="Number of servings")
    duration_minutes: Optional[int] = Field(None, description="Total cooking time in minutes")
    ingredients: list[IngredientDTO] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list, description="Cooking instructions")
    source_url: Optional[str] = Field(None, description="Original URL")
    image_url: Optional[str] = Field(None, description="Main image URL")
    confidence_score: float = Field(
        1.0, ge=0.0, le=1.0, description="Extraction confidence (0-1)"
    )


class ExtractionResult(BaseModel):
    """Result of a recipe extraction operation."""

    recipe: RecipeDTO
    extraction_method: str = Field(
        ..., description="Method used: 'jsonld', 'llm', or 'structured'"
    )
    provider_used: Optional[str] = Field(
        None, description="LLM provider used, if any"
    )
    model_used: Optional[str] = Field(
        None, description="Specific model used, if any"
    )
