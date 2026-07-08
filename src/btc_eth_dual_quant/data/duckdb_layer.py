"""DuckDB query/index layer over immutable raw envelopes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .storage import AppendOnlyRawStore, RawEnvelope


RAW_INDEX_DDL = """
CREATE TABLE IF NOT EXISTS raw_envelopes (
    dataset VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    endpoint VARCHAR NOT NULL,
    params_json VARCHAR NOT NULL,
    payload_json VARCHAR NOT NULL,
    ingested_at_ms BIGINT NOT NULL,
    content_sha256 VARCHAR NOT NULL,
    PRIMARY KEY (dataset, ingested_at_ms, content_sha256)
)
"""


class DuckDBLayer:
    """Maintains SQL query tables without mutating append-only raw storage."""

    def __init__(self, database_path: str | Path = "storage/duckdb/m0.duckdb") -> None:
        try:
            import duckdb  # type: ignore
        except ImportError as exc:
            raise RuntimeError("duckdb is required for the M0 query layer. Install project dependencies.") from exc
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._duckdb = duckdb

    def connect(self):
        con = self._duckdb.connect(str(self.database_path))
        con.execute(RAW_INDEX_DDL)
        return con

    def index_envelopes(self, envelopes: Iterable[RawEnvelope]) -> int:
        inserted = 0
        with self.connect() as con:
            for envelope in envelopes:
                con.execute(
                    """
                    INSERT OR IGNORE INTO raw_envelopes
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        envelope.dataset,
                        envelope.source,
                        envelope.endpoint,
                        json.dumps(envelope.params, ensure_ascii=False, sort_keys=True),
                        json.dumps(envelope.payload, ensure_ascii=False, sort_keys=True, default=str),
                        envelope.ingested_at_ms,
                        envelope.content_sha256,
                    ],
                )
                inserted += con.rowcount if con.rowcount and con.rowcount > 0 else 0
        return inserted

    def index_from_store(self, store: AppendOnlyRawStore, dataset: str) -> int:
        return self.index_envelopes(store.iter_envelopes(dataset))

    def create_derived_table(self, table: str, rows: list[dict[str, Any]]) -> int:
        """Append rows to a derived table, creating VARCHAR columns on first use."""

        if not rows:
            return 0
        columns = sorted(rows[0].keys())
        if any(sorted(row.keys()) != columns for row in rows):
            raise ValueError("all rows must have identical columns")
        quoted_cols = ", ".join(f'"{column}" VARCHAR' for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        with self.connect() as con:
            con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({quoted_cols})')
            con.executemany(
                f'INSERT INTO "{table}" ({", ".join(f"""\"{column}\"""" for column in columns)}) VALUES ({placeholders})',
                [[json.dumps(row[column], ensure_ascii=False, default=str) for column in columns] for row in rows],
            )
        return len(rows)
