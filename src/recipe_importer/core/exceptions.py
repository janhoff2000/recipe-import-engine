"""Custom exceptions for recipe import operations."""


class RecipeImportError(Exception):
    """Base exception for all recipe import errors."""


class FetchError(RecipeImportError):
    """Failed to fetch content from a URL."""


class PlatformNotSupportedError(FetchError):
    """The URL's platform is not supported."""


class PlatformRateLimitError(FetchError):
    """Platform rate limit exceeded."""


class PlatformAuthError(FetchError):
    """Authentication with platform failed (invalid/expired token)."""


class ContentNotFoundError(FetchError):
    """The requested content was not found (deleted, private, etc.)."""


class NoRecipeFoundError(RecipeImportError):
    """The content doesn't appear to contain a recipe."""


class ExtractionError(RecipeImportError):
    """LLM extraction failed or returned invalid data."""
