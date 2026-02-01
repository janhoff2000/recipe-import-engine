"""API request and response schemas."""

from pydantic import BaseModel, Field, HttpUrl

from recipe_importer.core.models import ExtractionResult


class ImportRequest(BaseModel):
    """Request to import a recipe from a URL."""

    url: HttpUrl = Field(..., description="URL to import recipe from")
    provider: str = Field("openai", description="LLM provider: openai, gemini, anthropic")
    model: str | None = Field(None, description="Specific model to use (optional)")
    skip_recipe_check: bool = Field(
        False,
        description="Skip heuristic recipe detection and force LLM extraction",
    )


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
    detail: str | None = None
