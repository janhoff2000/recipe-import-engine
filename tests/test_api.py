"""Tests for API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from recipe_importer.core.models import ExtractionResult, IngredientDTO, RecipeDTO
from recipe_importer.main import create_app
from recipe_importer.tracking.store import TrackingStore
from recipe_importer.tracking.tracker import Tracker


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = create_app()
    return app


@pytest.fixture
def client(app):
    """Create test client with mocked state."""
    # We need to set up app state manually since we skip lifespan
    mock_http_client = AsyncMock()
    mock_store = AsyncMock(spec=TrackingStore)
    mock_store.get_stats = AsyncMock(return_value=[])
    mock_store.get_comparison = AsyncMock(return_value=[])
    mock_store.get_records = AsyncMock(return_value=[])
    mock_store.get_trends = AsyncMock(return_value=[])
    mock_tracker = AsyncMock(spec=Tracker)

    app.state.http_client = mock_http_client
    app.state.tracking_store = mock_store
    app.state.tracker = mock_tracker

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestImportEndpoint:
    """Test /v1/import endpoint."""

    def test_import_success(self, client):
        mock_result = ExtractionResult(
            recipe=RecipeDTO(
                title="Test Recipe",
                ingredients=[IngredientDTO(name="flour", quantity=1.0, unit="cup")],
                steps=["Mix"],
            ),
            extraction_method="llm",
            provider_used="openai",
            model_used="gpt-4.1-nano",
        )

        with patch("recipe_importer.api.routes.create_pipeline") as mock_pipeline:
            pipeline_instance = AsyncMock()
            pipeline_instance.import_from_url = AsyncMock(return_value=mock_result)
            mock_pipeline.return_value = pipeline_instance

            response = client.post(
                "/v1/import",
                json={"url": "https://instagram.com/p/test123/"},
                headers={"X-Api-Key": "test"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["recipe"]["title"] == "Test Recipe"
        assert data["provider_used"] == "openai"

    def test_import_missing_url(self, client):
        response = client.post(
            "/v1/import",
            json={},
            headers={"X-Api-Key": "test"},
        )
        assert response.status_code == 422  # Validation error


class TestStatsEndpoints:
    """Test stats/tracking endpoints."""

    def test_get_stats(self, client):
        response = client.get(
            "/v1/stats",
            headers={"X-Api-Key": "test"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_comparison(self, client):
        response = client.get(
            "/v1/stats/comparison",
            headers={"X-Api-Key": "test"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_records(self, client):
        response = client.get(
            "/v1/stats/records",
            headers={"X-Api-Key": "test"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_records_with_params(self, client):
        response = client.get(
            "/v1/stats/records?model=gpt-4.1-nano&limit=10&offset=0",
            headers={"X-Api-Key": "test"},
        )
        assert response.status_code == 200

    def test_get_trends(self, client):
        response = client.get(
            "/v1/stats/trends",
            headers={"X-Api-Key": "test"},
        )
        assert response.status_code == 200


class TestTrackingEndpoints:
    """Test tracking report and corrections endpoints."""

    def test_report_extraction(self, client):
        from datetime import UTC, datetime

        from recipe_importer.tracking.models import ExtractionRecord

        mock_record = ExtractionRecord(
            id="test-id",
            timestamp=datetime.now(UTC),
            url="https://instagram.com/p/test/",
            platform="instagram",
            model="apple-intelligence",
            provider="apple",
            latency_ms=500,
            success=True,
            quality_score=0.8,
        )

        client.app.state.tracker.record_external_report = AsyncMock(return_value=mock_record)

        response = client.post(
            "/v1/tracking/report",
            json={
                "url": "https://instagram.com/p/test/",
                "platform": "instagram",
                "model": "apple-intelligence",
                "provider": "apple",
                "recipe": {
                    "title": "Test Recipe",
                    "ingredients": [{"name": "flour"}],
                    "steps": ["Mix"],
                },
                "latency_ms": 500,
            },
            headers={"X-Api-Key": "test"},
        )
        assert response.status_code == 201


class TestAdminDashboard:
    """Test admin dashboard."""

    def test_admin_serves_html(self, client):
        response = client.get("/admin")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Recipe Import Engine" in response.text
