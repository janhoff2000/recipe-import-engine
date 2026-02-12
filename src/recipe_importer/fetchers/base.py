"""Base fetcher protocol and shared models."""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class FetchResult(BaseModel):
    """Result from fetching content from a URL."""

    url: str = Field(..., description="Original URL that was fetched")
    platform: str = Field(..., description="Detected platform (instagram)")
    caption: str | None = Field(None, description="Caption/description text")
    title: str | None = Field(None, description="Post or video title")


@runtime_checkable
class Fetcher(Protocol):
    """Protocol for URL content fetchers."""

    def can_handle(self, url: str) -> bool:
        """Check if this fetcher can handle the given URL."""
        ...

    async def fetch(self, url: str) -> FetchResult:
        """Fetch content from the URL and return structured result."""
        ...
