# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, with dev deps)
uv pip install -e ".[dev]"

# Run dev server
uvicorn recipe_importer.main:app --reload

# Lint & format
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type check (strict mode)
basedpyright

# Run all tests
pytest

# Run single test file / specific test
pytest tests/test_tracking.py
pytest tests/test_pipeline.py::TestPipeline::test_import_happy_path

# Tests with coverage
pytest --cov

# Pre-commit (runs ruff + basedpyright + hygiene checks)
pre-commit run --all-files
```

## Architecture

FastAPI service that extracts recipes from Instagram URLs via LLM, with model comparison and tracking.

**Request flow:** `POST /v1/import` → `api/routes.py` → `core/pipeline.py` → fetcher → parser → LLM → `RecipeDTO`

**Key layers:**

- **API** (`api/`): Routes, request/response schemas, auth via `X-Api-Key` header. Auth is optional in dev (empty `api_key` setting = open access). Includes tracking/stats endpoints.
- **Pipeline** (`core/pipeline.py`): Orchestrates fetch → parse → extract. `create_pipeline()` factory auto-detects provider from model name. Includes retry logic and tracker integration.
- **Fetchers** (`fetchers/`): Protocol-based (`Fetcher` protocol in `base.py`). `InstagramFetcher` uses Meta oEmbed API v21.0. Accepts shared `httpx.AsyncClient`.
- **Parsers** (`parsers/caption.py`): Cleans Instagram captions (hashtag trimming, mention removal), heuristic `looks_like_recipe()` check.
- **LLM** (`llm/`): Protocol-based providers (OpenAI, Gemini). Factory in `llm/__init__.py` via `get_provider()` auto-detects from model prefix (`gpt-*` → OpenAI, `gemini-*` → Gemini). Both use **structured output** (Pydantic schema passed to API). Returns `ExtractionOutput` with recipe + token counts + latency.
- **Tracking** (`tracking/`): SQLite via `aiosqlite`. `TrackingStore` for persistence, `Tracker` for recording extractions, `quality.py` for automated scoring (0-1 composite), `pricing.py` for cost estimation.
- **Admin** (`admin/`): Single-page dashboard at `/admin` with Jinja2 + Chart.js. Consumes `/v1/stats` API endpoints.

**Config:** `pydantic-settings` in `config.py`, loaded from env vars / `.env` file, cached via `@lru_cache`. Key settings: `default_model`, provider API keys, `tracking_db_path`, `cors_origins`.

**Lifespan:** `main.py` uses FastAPI lifespan context manager to create/close shared httpx client + init tracking DB. Exception handlers map domain exceptions → HTTP status codes.

## Code Standards

- Python 3.14, line length 100
- `basedpyright` strict mode — all code must pass strict type checking
- Tests are exempt from type annotation rules (`ANN` ignored in `tests/`)
- `pytest-asyncio` with `asyncio_mode = "auto"` — async test functions work without decorators

## Models

- `gpt-4.1-nano` (default), `gpt-5-nano`, `gpt-5-mini` — OpenAI
- `gemini-2.5-flash-lite` — Google Gemini
- `apple-intelligence` — on-device (reported via tracking endpoint)
