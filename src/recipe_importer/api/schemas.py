"""API request and response schemas."""

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from recipe_importer.core.models import ExtractionResult


class ImportRequest(BaseModel):
    """Request to import a recipe from a URL."""

    url: HttpUrl = Field(..., description="URL to import recipe from")
    provider: str = Field("openai", description="LLM provider: openai, gemini, anthropic")
    model: Optional[str] = Field(None, description="Specific model to use (optional)")


class ImportResponse(ExtractionResult):
    """Response from recipe import."""

    pass


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
