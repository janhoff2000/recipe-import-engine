"""Automated quality scoring for recipe extractions."""

from recipe_importer.core.models import RecipeDTO


def compute_quality_score(recipe: RecipeDTO) -> dict[str, float | int | bool]:
    """Compute automated quality metrics from an extracted recipe.

    Returns a dict with:
    - quality_score: 0.0-1.0 composite score
    - fields_filled: count of optional fields that have values
    - fields_total: total optional fields checked
    - ingredient_count: number of ingredients
    - step_count: number of steps
    - has_quantities: whether ingredients have quantity+unit
    """
    # Completeness (40%): % of optional fields filled
    optional_fields = ["servings", "duration_minutes", "source_url"]
    fields_total = len(optional_fields)
    fields_filled = sum(1 for f in optional_fields if getattr(recipe, f) is not None)
    completeness = fields_filled / fields_total if fields_total > 0 else 0.0

    # Ingredient quality (30%): % of ingredients with quantity and unit
    ingredient_count = len(recipe.ingredients)
    if ingredient_count > 0:
        with_quantities = sum(
            1 for ing in recipe.ingredients if ing.quantity is not None and ing.unit is not None
        )
        ingredient_quality = with_quantities / ingredient_count
        has_quantities = with_quantities > 0
    else:
        ingredient_quality = 0.0
        has_quantities = False

    # Step quality (20%): has steps, reasonable count, meaningful length
    step_count = len(recipe.steps)
    step_quality = 0.0
    if step_count > 0:
        # Count in reasonable range (2-30)
        count_score = 1.0 if 2 <= step_count <= 30 else 0.5
        # Steps have meaningful length (>10 chars on average)
        avg_length = sum(len(s) for s in recipe.steps) / step_count
        length_score = min(1.0, avg_length / 20.0)
        step_quality = (count_score + length_score) / 2.0

    # Structure (10%): title present and reasonable length
    structure = 0.0
    if recipe.title:
        title_len = len(recipe.title.strip())
        if 3 <= title_len <= 200:
            structure = 1.0
        elif title_len > 0:
            structure = 0.5

    quality_score = (
        completeness * 0.4 + ingredient_quality * 0.3 + step_quality * 0.2 + structure * 0.1
    )

    return {
        "quality_score": round(quality_score, 4),
        "fields_filled": fields_filled,
        "fields_total": fields_total,
        "ingredient_count": ingredient_count,
        "step_count": step_count,
        "has_quantities": has_quantities,
    }
