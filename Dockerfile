FROM python:3.14-slim AS builder

RUN pip install uv

WORKDIR /app
COPY pyproject.toml .
RUN uv pip install --system --no-cache .

FROM python:3.14-slim

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY src/ src/

RUN mkdir -p data && chown appuser:appuser data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "recipe_importer.main:app", "--host", "0.0.0.0", "--port", "8000"]
