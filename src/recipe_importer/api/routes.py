"""API routes for recipe import and tracking."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from recipe_importer import __version__
from recipe_importer.api.auth import verify_api_key
from recipe_importer.api.schemas import (
    CorrectionsRequest,
    ErrorResponse,
    HealthResponse,
    ImportRequest,
    ImportResponse,
    TrackingReportRequest,
)
from recipe_importer.config import get_settings
from recipe_importer.core.pipeline import create_pipeline
from recipe_importer.tracking.models import ExtractionRecord, ModelStats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", version=__version__)


@router.post(
    "/v1/import",
    response_model=ImportResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def import_recipe(
    request_body: ImportRequest,
    request: Request,
    _api_key: str = Depends(verify_api_key),
) -> ImportResponse:
    """Import a recipe from a URL."""
    settings = get_settings()
    model = request_body.model or settings.default_model

    pipeline = create_pipeline(
        model=model,
        meta_app_token=settings.effective_meta_token,
        http_client=request.state.http_client,
        tracker=request.state.tracker,
    )

    result = await pipeline.import_from_url(
        str(request_body.url),
        skip_recipe_check=request_body.skip_recipe_check,
    )

    return ImportResponse(
        recipe=result.recipe,
        extraction_method=result.extraction_method,
        provider_used=result.provider_used,
        model_used=result.model_used,
    )


# --- Tracking / Stats endpoints ---


@router.get("/v1/stats", response_model=list[ModelStats])
async def get_stats(
    request: Request,
    model: str | None = Query(None),
    _api_key: str = Depends(verify_api_key),
) -> list[ModelStats]:
    """Get per-model aggregated stats."""
    store = request.state.tracking_store
    return await store.get_stats(model=model)


@router.get("/v1/stats/comparison", response_model=list[ModelStats])
async def get_comparison(
    request: Request,
    _api_key: str = Depends(verify_api_key),
) -> list[ModelStats]:
    """Get all models side by side for comparison."""
    store = request.state.tracking_store
    return await store.get_comparison()


@router.get("/v1/stats/records", response_model=list[ExtractionRecord])
async def get_records(
    request: Request,
    model: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _api_key: str = Depends(verify_api_key),
) -> list[ExtractionRecord]:
    """Get paginated extraction history."""
    store = request.state.tracking_store
    return await store.get_records(limit=limit, offset=offset, model=model)


@router.get("/v1/stats/trends")
async def get_trends(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    _api_key: str = Depends(verify_api_key),
) -> list[dict[str, str | float | int]]:
    """Get daily aggregated trends for charts."""
    store = request.state.tracking_store
    return await store.get_trends(days=days)


@router.post("/v1/tracking/report", response_model=ExtractionRecord, status_code=201)
async def report_extraction(
    body: TrackingReportRequest,
    request: Request,
    _api_key: str = Depends(verify_api_key),
) -> ExtractionRecord:
    """Report an extraction result from an external client."""
    tracker = request.state.tracker
    return await tracker.record_external_report(
        url=body.url,
        platform=body.platform,
        model=body.model,
        provider=body.provider,
        recipe=body.recipe,
        latency_ms=body.latency_ms,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
    )


@router.patch("/v1/tracking/{record_id}/corrections", response_model=ExtractionRecord)
async def report_corrections(
    record_id: str,
    body: CorrectionsRequest,
    request: Request,
    _api_key: str = Depends(verify_api_key),
) -> ExtractionRecord:
    """Report user edits as a quality signal."""
    store = request.state.tracking_store
    updated = await store.update_corrections(
        record_id=record_id,
        fields_corrected=body.fields_corrected,
        human_quality_score=body.human_quality_score,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record {record_id} not found",
        )
    record = await store.get_record(record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record {record_id} not found",
        )
    return record
