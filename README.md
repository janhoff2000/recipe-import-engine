# Recipe Import Engine

Recipe extraction service with model comparison, tracking, and an admin dashboard.

## Features

- Extract recipes from Instagram posts via LLM-powered caption analysis
- **Model comparison**: Track and compare OpenAI GPT-4.1 Nano, GPT-5 Nano, GPT-5 Mini, Gemini 2.5 Flash Lite, and Apple Intelligence
- **Structured output**: All providers use schema-enforced responses — no JSON parsing failures
- **Tracking system**: SQLite-backed extraction analytics with automated quality scoring
- **Admin dashboard**: Built-in web dashboard at `/admin` with Chart.js visualizations
- **Human quality signals**: Corrections endpoint to capture user edits as quality feedback
- **External reporting**: API for clients to report extraction results (e.g., on-device Apple Intelligence)

## Quick Start

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run the server
uvicorn recipe_importer.main:app --reload

# View API docs
open http://localhost:8000/docs

# View admin dashboard
open http://localhost:8000/admin
```

## API Endpoints

### Recipe Import

```bash
curl -X POST http://localhost:8000/v1/import \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your-service-key" \
  -d '{"url": "https://instagram.com/p/ABC123/", "model": "gpt-4.1-nano"}'
```

### Stats & Tracking

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/stats` | GET | Per-model aggregated stats |
| `/v1/stats/comparison` | GET | All models side by side |
| `/v1/stats/records` | GET | Paginated extraction history |
| `/v1/stats/trends` | GET | Daily aggregated trends |
| `/v1/tracking/report` | POST | Report external extraction results |
| `/v1/tracking/{id}/corrections` | PATCH | Report user edits as quality signal |
| `/admin` | GET | Admin dashboard |
| `/health` | GET | Health check |

### Models

| Model | Provider | Description |
|-------|----------|-------------|
| `gpt-4.1-nano` | OpenAI | Cheapest OpenAI option |
| `gpt-5-nano` | OpenAI | Next-gen cheap |
| `gpt-5-mini` | OpenAI | Next-gen mid-tier |
| `gemini-2.5-flash-lite` | Gemini | Google's fast/cheap |
| `apple-intelligence` | Apple | On-device (MyReciPal only) |

## Architecture

```
src/recipe_importer/
├── main.py           # FastAPI app with lifespan, exception handlers
├── config.py         # pydantic-settings configuration
├── api/              # Routes, schemas, auth
├── core/             # Pipeline, models, exceptions
├── fetchers/         # Instagram oEmbed fetcher
├── parsers/          # Caption cleaning & recipe detection
├── llm/              # OpenAI + Gemini providers (structured output)
├── tracking/         # SQLite store, quality scoring, pricing, tracker
└── admin/            # Dashboard (Jinja2 + Chart.js)
```

## Tracking Dimensions

| Dimension | How |
|-----------|-----|
| **Cost** | Token counts from API response metadata + pricing table |
| **Latency** | Wall-clock ms from LLM call to response |
| **Reliability** | Success rate, retry count, error classification |
| **Quality (automated)** | Composite 0-1 score: completeness, ingredient quality, step quality |
| **Quality (human)** | User edits recipe → diff reported via corrections endpoint |

## Docker

```bash
docker build -t recipe-import-engine .
docker run -p 8000:8000 -v ./data:/app/data --env-file .env recipe-import-engine
```

## License

MIT
