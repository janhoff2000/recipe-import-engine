"""Tracking data models."""

from datetime import datetime

from pydantic import BaseModel, Field


class ExtractionRecord(BaseModel):
    """Record of a single recipe extraction for analytics."""

    id: str = Field(..., description="UUID")
    timestamp: datetime
    url: str
    platform: str  # "instagram"
    model: str  # "gpt-4.1-nano", "apple-intelligence", etc.
    provider: str  # "openai", "gemini", "apple"

    # Cost
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None

    # Latency
    latency_ms: int = 0

    # Reliability
    success: bool = True
    error_type: str | None = None  # "timeout", "api_error", "validation"
    retry_count: int = 0

    # Quality (automated)
    quality_score: float = 0.0  # 0.0-1.0 composite
    fields_filled: int = 0
    fields_total: int = 0
    ingredient_count: int = 0
    step_count: int = 0
    has_quantities: bool = False

    # Quality (human — updated later via corrections endpoint)
    human_edited: bool | None = None
    fields_corrected: int | None = None
    human_quality_score: float | None = None

    # Quality (LLM-as-judge — optional)
    judge_score: float | None = None


class ModelStats(BaseModel):
    """Aggregated statistics for a single model."""

    model: str
    provider: str
    total_extractions: int = 0
    success_count: int = 0
    success_rate: float = 0.0
    avg_latency_ms: float = 0.0
    avg_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    avg_quality_score: float = 0.0
    avg_human_quality_score: float | None = None
    avg_input_tokens: float = 0.0
    avg_output_tokens: float = 0.0
