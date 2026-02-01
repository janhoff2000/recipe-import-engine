"""Base fetcher protocol and shared models."""

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class FetchResult(BaseModel):
    """Result from fetching content from a URL."""

    url: str = Field(..., description="Original URL that was fetched")
    platform: str = Field(..., description="Detected platform (instagram, tiktok, youtube, blog)")
    caption: str | None = Field(None, description="Caption/description text")
    title: str | None = Field(None, description="Post or video title")
    image_url: str | None = Field(None, description="Main image URL if available")
    author: str | None = Field(None, description="Content author/creator")


@runtime_checkable
class Fetcher(Protocol):
    """Protocol for URL content fetchers.

    Each platform (Instagram, TikTok, etc.) implements this protocol.
    Using Protocol enables structural subtyping - no inheritance required.
    """

    def can_handle(self, url: str) -> bool:
        """Check if this fetcher can handle the given URL."""
        ...

    async def fetch(self, url: str) -> FetchResult:
        """Fetch content from the URL and return structured result."""
        ...
