"""API request and response schemas."""

from pydantic import BaseModel, Field, HttpUrl

from recipe_importer.core.models import ExtractionResult, RecipeDTO
from recipe_importer.tracking.models import ExtractionRecord, ModelStats


class ImportRequest(BaseModel):
    """Request to import a recipe from a URL."""

    url: HttpUrl = Field(..., description="URL to import recipe from")
    model: str | None = Field(None, description="Model to use (auto-detects provider)")
    skip_recipe_check: bool = Field(
        False,
        description="Skip heuristic recipe detection and force LLM extraction",
    )


class ImportResponse(ExtractionResult):
    """Response from recipe import."""


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: str | None = None


class StatsResponse(BaseModel):
    """Model stats response."""

    stats: list[ModelStats]


class ComparisonResponse(BaseModel):
    """Model comparison response."""

    models: list[ModelStats]


class RecordsResponse(BaseModel):
    """Paginated records response."""

    records: list[ExtractionRecord]
    total: int


class TrackingReportRequest(BaseModel):
    """External tracking report (e.g., Apple Intelligence results)."""

    url: str
    platform: str = "instagram"
    model: str
    provider: str
    recipe: RecipeDTO
    latency_ms: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None


class CorrectionsRequest(BaseModel):
    """User correction report."""

    fields_corrected: int = Field(..., ge=0)
    human_quality_score: float = Field(..., ge=0.0, le=1.0)
