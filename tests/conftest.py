"""Test configuration and fixtures."""

import pytest


@pytest.fixture
def sample_recipe_text() -> str:
    """Sample recipe text for testing extraction."""
    return """
    Easy Chocolate Chip Cookies 🍪

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
    1. Preheat oven to 375°F (190°C)
    2. Mix flour, baking soda, and salt in a bowl
    3. In another bowl, cream butter and sugars until fluffy
    4. Beat in eggs and vanilla
    5. Gradually blend in flour mixture
    6. Stir in chocolate chips
    7. Drop rounded tablespoons onto baking sheets
    8. Bake 9-11 minutes until golden brown
    9. Cool on baking sheet for 2 minutes, then transfer to wire rack
    """
