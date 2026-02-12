"""Fetchers module — URL content fetchers."""

from recipe_importer.fetchers.base import Fetcher, FetchResult
from recipe_importer.fetchers.instagram import InstagramFetcher

__all__ = [
    "FetchResult",
    "Fetcher",
    "InstagramFetcher",
]
