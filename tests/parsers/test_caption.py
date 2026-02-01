"""Tests for caption parser."""

import pytest

from recipe_importer.parsers.caption import (
    clean_caption,
    looks_like_recipe,
    prepare_for_extraction,
)


class TestCleanCaption:
    """Test caption cleaning."""

    def test_removes_excess_hashtags(self):
        """Should keep only first 3 hashtags."""
        caption = "Great recipe! #food #cooking #dinner #tasty #yummy #delicious"
        cleaned = clean_caption(caption)
        assert cleaned.count("#") == 3
        assert "#food" in cleaned
        assert "#cooking" in cleaned
        assert "#dinner" in cleaned
        assert "#tasty" not in cleaned

    def test_removes_mentions(self):
        """Should remove @ mentions."""
        caption = "Thanks @chef_john for this recipe! @foodnetwork"
        cleaned = clean_caption(caption)
        assert "@" not in cleaned
        assert "Thanks" in cleaned
        assert "for this recipe!" in cleaned

    def test_normalizes_whitespace(self):
        """Should normalize multiple spaces and newlines."""
        caption = "Step 1:   Mix ingredients\n\n\nStep 2:  Bake"
        cleaned = clean_caption(caption)
        assert "  " not in cleaned
        assert "\n" not in cleaned

    def test_empty_caption(self) -> None:
        """Should handle empty input."""
        assert clean_caption("") == ""


class TestLooksLikeRecipe:
    """Test recipe detection heuristics."""

    @pytest.mark.parametrize(
        "caption",
        [
            "Here's my recipe for chocolate cake!",
            "Ingredients: flour, sugar, eggs",
            "Instructions: 1. Preheat oven 2. Mix ingredients",
            "This dish serves 4 people",
            "Prep time: 30 minutes",
            "Add 2 cups flour and 1 tsp salt",
            "1. Mix the flour 2. Add eggs 3. Bake",
            "Preheat oven to 350°F",
            "Simmer for 20 minutes",
        ],
    )
    def test_detects_recipe_content(self, caption: str):
        """Should detect recipe-related content."""
        assert looks_like_recipe(caption) is True

    @pytest.mark.parametrize(
        "caption",
        [
            "Beautiful sunset! 🌅",
            "Having fun at the beach",
            "New shoes arrived today",
            "Happy birthday mom!",
            "",
        ],
    )
    def test_rejects_non_recipe_content(self, caption: str):
        """Should reject non-recipe content."""
        assert looks_like_recipe(caption) is False

    def test_numbered_steps_detection(self):
        """Should detect numbered cooking steps."""
        assert looks_like_recipe("1. Chop onions 2. Fry in oil") is True
        assert looks_like_recipe("1) Add flour 2) Mix well") is True

    def test_measurement_detection(self):
        """Should detect measurement patterns."""
        assert looks_like_recipe("Add 2 cups of flour") is True
        assert looks_like_recipe("Use 1/2 tsp of salt") is True
        assert looks_like_recipe("Need 100g butter") is True


class TestPrepareForExtraction:
    """Test extraction preparation."""

    def test_adds_context_for_short_captions(self):
        """Should add context prefix for informal captions."""
        caption = "Best brownies ever! Mix flour, cocoa, butter"
        prepared = prepare_for_extraction(caption)
        assert prepared.startswith("Recipe from social media post:")
        assert "brownies" in prepared

    def test_no_context_for_structured_captions(self):
        """Should not add context for already structured recipes."""
        caption = "Ingredients: flour, sugar. Instructions: mix and bake."
        prepared = prepare_for_extraction(caption)
        assert not prepared.startswith("Recipe from social media post:")

    def test_empty_caption(self):
        """Should handle empty input."""
        assert prepare_for_extraction("") == ""
