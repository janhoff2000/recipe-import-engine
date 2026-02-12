"""Test configuration and fixtures."""

import tempfile
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from recipe_importer.core.models import IngredientDTO, RecipeDTO
from recipe_importer.llm.base import ExtractionOutput
from recipe_importer.tracking.store import TrackingStore
from recipe_importer.tracking.tracker import Tracker


@pytest.fixture
def sample_recipe_text() -> str:
    """Sample recipe text for testing extraction."""
    return """
    Easy Chocolate Chip Cookies

    Makes 24 cookies

    Ingredients:
    - 2 cups all-purpose flour
    - 1 cup butter, softened
    - 3/4 cup sugar
    - 1/2 cup brown sugar
    - 2 eggs
    - 1 tsp vanilla extract
    - 1 tsp baking soda
    - 1/2 tsp salt
    - 2 cups chocolate chips

    Instructions:
    1. Preheat oven to 375F (190C)
    2. Mix flour, baking soda, and salt in a bowl
    3. In another bowl, cream butter and sugars until fluffy
    4. Beat in eggs and vanilla
    5. Gradually blend in flour mixture
    6. Stir in chocolate chips
    7. Drop rounded tablespoons onto baking sheets
    8. Bake 9-11 minutes until golden brown
    9. Cool on baking sheet for 2 minutes, then transfer to wire rack
    """


@pytest.fixture
def sample_recipe_dto() -> RecipeDTO:
    """Sample RecipeDTO for testing."""
    return RecipeDTO(
        title="Chocolate Chip Cookies",
        servings=24,
        duration_minutes=30,
        ingredients=[
            IngredientDTO(name="all-purpose flour", quantity=2.0, unit="cups"),
            IngredientDTO(name="butter", quantity=1.0, unit="cup", note="softened"),
            IngredientDTO(name="sugar", quantity=0.75, unit="cup"),
            IngredientDTO(name="brown sugar", quantity=0.5, unit="cup"),
            IngredientDTO(name="eggs", quantity=2.0, unit=None),
            IngredientDTO(name="vanilla extract", quantity=1.0, unit="tsp"),
            IngredientDTO(name="baking soda", quantity=1.0, unit="tsp"),
            IngredientDTO(name="salt", quantity=0.5, unit="tsp"),
            IngredientDTO(name="chocolate chips", quantity=2.0, unit="cups"),
        ],
        steps=[
            "Preheat oven to 375F",
            "Mix flour, baking soda, and salt",
            "Cream butter and sugars until fluffy",
            "Beat in eggs and vanilla",
            "Gradually blend in flour mixture",
            "Stir in chocolate chips",
            "Drop rounded tablespoons onto baking sheets",
            "Bake 9-11 minutes until golden brown",
            "Cool and transfer to wire rack",
        ],
    )


@pytest.fixture
def sample_extraction_output(sample_recipe_dto) -> ExtractionOutput:
    """Sample ExtractionOutput for testing."""
    return ExtractionOutput(
        recipe=sample_recipe_dto,
        input_tokens=500,
        output_tokens=300,
        latency_ms=1200,
    )


@pytest.fixture
def mock_llm_provider(sample_extraction_output):
    """Mock LLM provider that returns sample output."""
    provider = MagicMock()
    provider.name = "openai"
    provider.model = "gpt-4.1-nano"
    provider.extract_recipe = AsyncMock(return_value=sample_extraction_output)
    return provider


@pytest.fixture
def mock_http_client():
    """Mock httpx.AsyncClient."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture
async def tracking_store() -> AsyncIterator[TrackingStore]:
    """Create a temporary tracking store for tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    store = TrackingStore(db_path)
    await store.init()
    yield store
    await store.close()


@pytest.fixture
async def tracker(tracking_store) -> Tracker:
    """Create a tracker with temporary store."""
    return Tracker(tracking_store)
