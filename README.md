# Recipe Import Engine

Multi-provider recipe extraction service with BYOK (Bring Your Own Key) support.

## Features

- Extract recipes from Instagram, TikTok, YouTube, and recipe blogs
- Multi-provider LLM support: OpenAI, Google Gemini, Anthropic
- BYOK: Users can provide their own API keys
- Deterministic JSON-LD parsing for blogs (no LLM needed)
- RESTful API with automatic OpenAPI documentation

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the server
uvicorn recipe_importer.main:app --reload

# View API docs
open http://localhost:8000/docs
```

## API Usage

```bash
curl -X POST http://localhost:8000/v1/import \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your-service-key" \
  -H "X-LLM-Api-Key: your-openai-key" \
  -d '{"url": "https://example.com/recipe", "provider": "openai"}'
```

## Project Structure

```
src/recipe_importer/
├── main.py           # FastAPI app entry
├── api/              # API routes and schemas
├── fetchers/         # URL content fetchers
├── parsers/          # JSON-LD and structured parsers
├── llm/              # LLM provider adapters
└── core/             # Domain models and pipeline
```

## License

MIT
