"""Tracker — wraps LLM calls to auto-record extraction metrics."""

import logging
import uuid
from datetime import UTC, datetime

from recipe_importer.core.models import RecipeDTO
from recipe_importer.llm.base import ExtractionOutput
from recipe_importer.tracking.models import ExtractionRecord
from recipe_importer.tracking.pricing import estimate_cost
from recipe_importer.tracking.quality import compute_quality_score
from recipe_importer.tracking.store import TrackingStore

logger = logging.getLogger(__name__)


class Tracker:
    """Records extraction results for analytics and model comparison."""

    def __init__(self, store: TrackingStore) -> None:
        self._store = store

    async def record_extraction(
        self,
        *,
        url: str,
        platform: str,
        model: str,
        provider: str,
        output: ExtractionOutput,
        retry_count: int = 0,
    ) -> ExtractionRecord:
        """Record a successful extraction."""
        quality = compute_quality_score(output.recipe)
        cost = estimate_cost(model, output.input_tokens, output.output_tokens)

        record = ExtractionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            url=url,
            platform=platform,
            model=model,
            provider=provider,
            input_tokens=output.input_tokens,
            output_tokens=output.output_tokens,
            estimated_cost_usd=cost,
            latency_ms=output.latency_ms,
            success=True,
            retry_count=retry_count,
            quality_score=quality["quality_score"],
            fields_filled=int(quality["fields_filled"]),
            fields_total=int(quality["fields_total"]),
            ingredient_count=int(quality["ingredient_count"]),
            step_count=int(quality["step_count"]),
            has_quantities=bool(quality["has_quantities"]),
        )

        await self._store.save(record)
        logger.info(
            "Recorded extraction: model=%s, latency=%dms, quality=%.2f, cost=$%.6f",
            model,
            output.latency_ms,
            record.quality_score,
            cost or 0.0,
        )
        return record

    async def record_failure(
        self,
        *,
        url: str,
        platform: str,
        model: str,
        provider: str,
        error_type: str,
        latency_ms: int = 0,
        retry_count: int = 0,
    ) -> ExtractionRecord:
        """Record a failed extraction."""
        record = ExtractionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            url=url,
            platform=platform,
            model=model,
            provider=provider,
            latency_ms=latency_ms,
            success=False,
            error_type=error_type,
            retry_count=retry_count,
        )

        await self._store.save(record)
        logger.warning(
            "Recorded failed extraction: model=%s, error=%s",
            model,
            error_type,
        )
        return record

    async def record_external_report(
        self,
        *,
        url: str,
        platform: str,
        model: str,
        provider: str,
        recipe: RecipeDTO,
        latency_ms: int = 0,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> ExtractionRecord:
        """Record an extraction reported by an external client (e.g. Apple Intelligence)."""
        quality = compute_quality_score(recipe)
        cost = (
            estimate_cost(model, input_tokens, output_tokens)
            if input_tokens is not None and output_tokens is not None
            else None
        )

        record = ExtractionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            url=url,
            platform=platform,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            latency_ms=latency_ms,
            success=True,
            quality_score=quality["quality_score"],
            fields_filled=int(quality["fields_filled"]),
            fields_total=int(quality["fields_total"]),
            ingredient_count=int(quality["ingredient_count"]),
            step_count=int(quality["step_count"]),
            has_quantities=bool(quality["has_quantities"]),
        )

        await self._store.save(record)
        logger.info("Recorded external report: model=%s, quality=%.2f", model, record.quality_score)
        return record
