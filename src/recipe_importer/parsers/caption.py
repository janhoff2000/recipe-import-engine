"""Caption parsing and recipe detection utilities."""

import re

RECIPE_KEYWORDS = frozenset(
    {
        "recipe",
        "ingredients",
        "ingredient",
        "instructions",
        "directions",
        "steps",
        "cook",
        "bake",
        "prep time",
        "cooking time",
        "servings",
        "serves",
        "tbsp",
        "tsp",
        "cup",
        "cups",
        "tablespoon",
        "teaspoon",
        "oven",
        "preheat",
        "mix",
        "stir",
        "chop",
        "dice",
        "simmer",
        "boil",
    }
)

HASHTAG_PATTERN = re.compile(r"#\w+")
MENTION_PATTERN = re.compile(r"@\w+")
EMOJI_PATTERN = re.compile(
    r"[\U0001F300-\U0001F9FF]|"  # Misc symbols and pictographs
    r"[\U0001FA00-\U0001FAFF]|"  # Chess, extended-A
    r"[\U00002600-\U000027BF]",  # Misc symbols
    re.UNICODE,
)


def clean_caption(caption: str) -> str:
    """Clean up caption text for LLM processing.

    - Removes excessive hashtags (keeps first 3)
    - Removes @ mentions
    - Normalizes whitespace
    - Keeps emojis (they can provide context)
    """
    if not caption:
        return ""

    # Extract hashtags and keep only first 3
    hashtags = HASHTAG_PATTERN.findall(caption)
    caption = HASHTAG_PATTERN.sub("", caption)
    if hashtags:
        caption = caption.rstrip() + " " + " ".join(hashtags[:3])

    # Remove mentions
    caption = MENTION_PATTERN.sub("", caption)

    # Normalize whitespace
    caption = " ".join(caption.split())

    return caption.strip()


def looks_like_recipe(caption: str) -> bool:
    """Heuristic check if caption likely contains a recipe.

    Returns True if the caption contains recipe-related keywords
    or patterns suggesting cooking instructions.
    """
    if not caption:
        return False

    caption_lower = caption.lower()

    # Check for recipe keywords
    for keyword in RECIPE_KEYWORDS:
        if keyword in caption_lower:
            return True

    # Check for numbered steps (1., 2., etc. or 1) 2) etc.)
    if re.search(r"\b[1-9]\s*[.):]\s*\w", caption):
        return True

    # Check for measurement patterns (e.g., "2 cups", "1/2 tsp")
    if re.search(r"\b\d+(?:/\d+)?\s*(?:cup|tbsp|tsp|oz|g|ml|lb)", caption_lower):
        return True

    return False


def prepare_for_extraction(caption: str) -> str:
    """Prepare caption text for LLM extraction.

    Cleans the caption and adds context for the LLM.
    """
    cleaned = clean_caption(caption)

    if not cleaned:
        return ""

    # Add context prefix if caption seems informal
    if len(cleaned) < 500 and not any(
        marker in cleaned.lower() for marker in ["ingredients:", "instructions:", "steps:"]
    ):
        return f"Recipe from social media post:\n\n{cleaned}"

    return cleaned
