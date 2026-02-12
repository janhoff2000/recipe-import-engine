"""Tests for the tracking system."""

import uuid
from datetime import UTC, datetime

from recipe_importer.core.models import IngredientDTO, RecipeDTO
from recipe_importer.tracking.models import ExtractionRecord
from recipe_importer.tracking.pricing import estimate_cost
from recipe_importer.tracking.quality import compute_quality_score


class TestQualityScoring:
    """Test automated quality scoring."""

    def test_high_quality_recipe(self, sample_recipe_dto):
        result = compute_quality_score(sample_recipe_dto)
        assert result["quality_score"] > 0.7
        assert result["ingredient_count"] == 9
        assert result["step_count"] == 9
        assert result["has_quantities"] is True

    def test_minimal_recipe(self):
        recipe = RecipeDTO(
            title="Toast",
            ingredients=[IngredientDTO(name="bread")],
            steps=["Toast it"],
        )
        result = compute_quality_score(recipe)
        assert result["quality_score"] < 0.5
        assert result["fields_filled"] == 0
        assert result["has_quantities"] is False

    def test_empty_recipe(self):
        recipe = RecipeDTO(title="", ingredients=[], steps=[])
        result = compute_quality_score(recipe)
        assert result["quality_score"] == 0.0
        assert result["ingredient_count"] == 0

    def test_completeness_with_all_optional_fields(self):
        recipe = RecipeDTO(
            title="Full Recipe",
            servings=4,
            duration_minutes=30,
            source_url="https://example.com",
            ingredients=[IngredientDTO(name="flour", quantity=2.0, unit="cups")],
            steps=["Mix well", "Bake for 20 minutes"],
        )
        result = compute_quality_score(recipe)
        assert result["fields_filled"] == 3
        assert result["fields_total"] == 3


class TestPricing:
    """Test cost estimation."""

    def test_known_model(self):
        cost = estimate_cost("gpt-4.1-nano", 1000, 500)
        assert cost is not None
        # (1000 * 0.10 + 500 * 0.40) / 1_000_000 = 0.0003
        assert abs(cost - 0.0003) < 0.0001

    def test_unknown_model(self):
        assert estimate_cost("unknown-model", 1000, 500) is None

    def test_zero_tokens(self):
        cost = estimate_cost("gpt-4.1-nano", 0, 0)
        assert cost == 0.0


class TestTrackingStore:
    """Test SQLite tracking store."""

    async def test_save_and_retrieve(self, tracking_store):
        record = ExtractionRecord(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            url="https://instagram.com/p/test123/",
            platform="instagram",
            model="gpt-4.1-nano",
            provider="openai",
            input_tokens=500,
            output_tokens=300,
            estimated_cost_usd=0.0003,
            latency_ms=1200,
            success=True,
            quality_score=0.85,
            fields_filled=2,
            fields_total=3,
            ingredient_count=9,
            step_count=9,
            has_quantities=True,
        )
        await tracking_store.save(record)

        retrieved = await tracking_store.get_record(record.id)
        assert retrieved is not None
        assert retrieved.id == record.id
        assert retrieved.model == "gpt-4.1-nano"
        assert retrieved.success is True

    async def test_get_records_paginated(self, tracking_store):
        for i in range(5):
            record = ExtractionRecord(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                url=f"https://instagram.com/p/test{i}/",
                platform="instagram",
                model="gpt-4.1-nano",
                provider="openai",
                latency_ms=1000 + i * 100,
                success=True,
                quality_score=0.8,
            )
            await tracking_store.save(record)

        records = await tracking_store.get_records(limit=3)
        assert len(records) == 3

        records_all = await tracking_store.get_records(limit=10)
        assert len(records_all) == 5

    async def test_get_stats(self, tracking_store):
        for model in ["gpt-4.1-nano", "gpt-4.1-nano", "gemini-2.5-flash-lite"]:
            provider = "openai" if model.startswith("gpt") else "gemini"
            record = ExtractionRecord(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                url="https://instagram.com/p/test/",
                platform="instagram",
                model=model,
                provider=provider,
                latency_ms=1000,
                success=True,
                quality_score=0.8,
            )
            await tracking_store.save(record)

        stats = await tracking_store.get_stats()
        assert len(stats) == 2  # Two distinct models

        nano_stats = await tracking_store.get_stats(model="gpt-4.1-nano")
        assert len(nano_stats) == 1
        assert nano_stats[0].total_extractions == 2

    async def test_update_corrections(self, tracking_store):
        record_id = str(uuid.uuid4())
        record = ExtractionRecord(
            id=record_id,
            timestamp=datetime.now(UTC),
            url="https://instagram.com/p/test/",
            platform="instagram",
            model="gpt-4.1-nano",
            provider="openai",
            latency_ms=1000,
            success=True,
            quality_score=0.8,
        )
        await tracking_store.save(record)

        updated = await tracking_store.update_corrections(record_id, 3, 0.7)
        assert updated is True

        retrieved = await tracking_store.get_record(record_id)
        assert retrieved is not None
        assert retrieved.human_edited is True
        assert retrieved.fields_corrected == 3
        assert retrieved.human_quality_score == 0.7

    async def test_update_corrections_nonexistent(self, tracking_store):
        updated = await tracking_store.update_corrections("nonexistent-id", 1, 0.5)
        assert updated is False

    async def test_get_comparison(self, tracking_store):
        comparison = await tracking_store.get_comparison()
        assert isinstance(comparison, list)


class TestTracker:
    """Test the Tracker wrapper."""

    async def test_record_extraction(self, tracker, sample_extraction_output):
        record = await tracker.record_extraction(
            url="https://instagram.com/p/test/",
            platform="instagram",
            model="gpt-4.1-nano",
            provider="openai",
            output=sample_extraction_output,
        )
        assert record.success is True
        assert record.model == "gpt-4.1-nano"
        assert record.quality_score > 0

    async def test_record_failure(self, tracker):
        record = await tracker.record_failure(
            url="https://instagram.com/p/test/",
            platform="instagram",
            model="gpt-4.1-nano",
            provider="openai",
            error_type="timeout",
        )
        assert record.success is False
        assert record.error_type == "timeout"

    async def test_record_external_report(self, tracker, sample_recipe_dto):
        record = await tracker.record_external_report(
            url="https://instagram.com/p/test/",
            platform="instagram",
            model="apple-intelligence",
            provider="apple",
            recipe=sample_recipe_dto,
            latency_ms=500,
        )
        assert record.model == "apple-intelligence"
        assert record.provider == "apple"
        assert record.quality_score > 0
