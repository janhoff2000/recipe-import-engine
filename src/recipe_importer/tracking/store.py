"""SQLite storage for extraction tracking records."""

from pathlib import Path

import aiosqlite

from recipe_importer.tracking.models import ExtractionRecord, ModelStats

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS extraction_records (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    url TEXT NOT NULL,
    platform TEXT NOT NULL,
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    estimated_cost_usd REAL,
    latency_ms INTEGER NOT NULL DEFAULT 0,
    success INTEGER NOT NULL DEFAULT 1,
    error_type TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    quality_score REAL NOT NULL DEFAULT 0.0,
    fields_filled INTEGER NOT NULL DEFAULT 0,
    fields_total INTEGER NOT NULL DEFAULT 0,
    ingredient_count INTEGER NOT NULL DEFAULT 0,
    step_count INTEGER NOT NULL DEFAULT 0,
    has_quantities INTEGER NOT NULL DEFAULT 0,
    human_edited INTEGER,
    fields_corrected INTEGER,
    human_quality_score REAL,
    judge_score REAL
)
"""

CREATE_INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_records_model ON extraction_records(model)",
    "CREATE INDEX IF NOT EXISTS idx_records_timestamp ON extraction_records(timestamp)",
]


class TrackingStore:
    """SQLite-backed storage for extraction tracking records."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init(self) -> None:
        """Initialize database and create tables."""
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute(CREATE_TABLE_SQL)
        for index_sql in CREATE_INDEX_SQL:
            await self._db.execute(index_sql)
        await self._db.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def _conn(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("TrackingStore not initialized. Call init() first.")
        return self._db

    async def save(self, record: ExtractionRecord) -> None:
        """Save an extraction record."""
        data = record.model_dump()
        data["timestamp"] = record.timestamp.isoformat()
        data["success"] = int(data["success"])
        data["has_quantities"] = int(data["has_quantities"])
        if data["human_edited"] is not None:
            data["human_edited"] = int(data["human_edited"])

        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data)
        await self._conn.execute(
            f"INSERT INTO extraction_records ({columns}) VALUES ({placeholders})",
            data,
        )
        await self._conn.commit()

    async def update_corrections(
        self,
        record_id: str,
        fields_corrected: int,
        human_quality_score: float,
    ) -> bool:
        """Update a record with user correction data."""
        cursor = await self._conn.execute(
            """UPDATE extraction_records
            SET human_edited = 1, fields_corrected = :fields_corrected,
                human_quality_score = :human_quality_score
            WHERE id = :id""",
            {
                "id": record_id,
                "fields_corrected": fields_corrected,
                "human_quality_score": human_quality_score,
            },
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def update_judge_score(self, record_id: str, score: float) -> bool:
        """Update a record with LLM-as-judge score."""
        cursor = await self._conn.execute(
            "UPDATE extraction_records SET judge_score = :score WHERE id = :id",
            {"id": record_id, "score": score},
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def get_stats(self, model: str | None = None) -> list[ModelStats]:
        """Get aggregated stats, optionally filtered by model."""
        where_clause = "WHERE model = :model" if model else ""
        params: dict[str, str] = {"model": model} if model else {}

        query = f"""
        SELECT
            model,
            provider,
            COUNT(*) as total_extractions,
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
            AVG(latency_ms) as avg_latency_ms,
            AVG(estimated_cost_usd) as avg_cost_usd,
            SUM(estimated_cost_usd) as total_cost_usd,
            AVG(CASE WHEN success = 1 THEN quality_score END) as avg_quality_score,
            AVG(human_quality_score) as avg_human_quality_score,
            AVG(input_tokens) as avg_input_tokens,
            AVG(output_tokens) as avg_output_tokens
        FROM extraction_records
        {where_clause}
        GROUP BY model, provider
        ORDER BY model
        """

        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()

        results: list[ModelStats] = []
        for row in rows:
            total = row["total_extractions"]
            success = row["success_count"]
            results.append(
                ModelStats(
                    model=row["model"],
                    provider=row["provider"],
                    total_extractions=total,
                    success_count=success,
                    success_rate=success / total if total > 0 else 0.0,
                    avg_latency_ms=row["avg_latency_ms"] or 0.0,
                    avg_cost_usd=row["avg_cost_usd"] or 0.0,
                    total_cost_usd=row["total_cost_usd"] or 0.0,
                    avg_quality_score=row["avg_quality_score"] or 0.0,
                    avg_human_quality_score=row["avg_human_quality_score"],
                    avg_input_tokens=row["avg_input_tokens"] or 0.0,
                    avg_output_tokens=row["avg_output_tokens"] or 0.0,
                )
            )
        return results

    async def get_comparison(self) -> list[ModelStats]:
        """Get all models side by side."""
        return await self.get_stats()

    async def get_records(
        self,
        limit: int = 50,
        offset: int = 0,
        model: str | None = None,
    ) -> list[ExtractionRecord]:
        """Get paginated extraction records."""
        where_clause = "WHERE model = :model" if model else ""
        params: dict[str, str | int] = {"limit": limit, "offset": offset}
        if model:
            params["model"] = model

        query = f"""
        SELECT * FROM extraction_records
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
        """

        cursor = await self._conn.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_record(row) for row in rows]

    def _row_to_record(self, row: aiosqlite.Row) -> ExtractionRecord:
        """Convert a database row to an ExtractionRecord."""
        data = dict(row)
        data["success"] = bool(data["success"])
        data["has_quantities"] = bool(data["has_quantities"])
        if data["human_edited"] is not None:
            data["human_edited"] = bool(data["human_edited"])
        return ExtractionRecord.model_validate(data)

    async def get_record(self, record_id: str) -> ExtractionRecord | None:
        """Get a single record by ID."""
        cursor = await self._conn.execute(
            "SELECT * FROM extraction_records WHERE id = :id",
            {"id": record_id},
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    async def get_trends(
        self,
        days: int = 30,
    ) -> list[dict[str, str | float | int]]:
        """Get daily aggregated trends for dashboard charts."""
        query = """
        SELECT
            DATE(timestamp) as date,
            model,
            COUNT(*) as count,
            AVG(CASE WHEN success = 1 THEN quality_score END) as avg_quality,
            AVG(latency_ms) as avg_latency
        FROM extraction_records
        WHERE timestamp >= datetime('now', :days_ago)
        GROUP BY DATE(timestamp), model
        ORDER BY date
        """
        cursor = await self._conn.execute(query, {"days_ago": f"-{days} days"})
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
