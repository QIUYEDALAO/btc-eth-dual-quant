"""Append-only raw storage for exchange responses."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATASET_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def validate_dataset_name(dataset: str) -> str:
    if not DATASET_NAME_RE.fullmatch(dataset) or ".." in dataset:
        raise ValueError(f"invalid dataset name: {dataset!r}")
    return dataset


def utc_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def utc_date_path(ts_ms: int | None = None) -> str:
    ts = datetime.fromtimestamp((ts_ms or utc_ms()) / 1000, tz=timezone.utc)
    return f"year={ts:%Y}/month={ts:%m}/day={ts:%d}"


@dataclass(frozen=True)
class RawEnvelope:
    dataset: str
    source: str
    endpoint: str
    params: dict[str, Any]
    payload: Any
    ingested_at_ms: int
    content_sha256: str

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True)


class AppendOnlyRawStore:
    """Stores immutable response envelopes as JSONL files under `storage/raw`."""

    def __init__(self, root: str | Path = "storage/raw") -> None:
        self.root = Path(root)

    def append(
        self,
        dataset: str,
        source: str,
        endpoint: str,
        params: dict[str, Any],
        payload: Any,
    ) -> RawEnvelope:
        validate_dataset_name(dataset)
        ingested_at_ms = utc_ms()
        canonical_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
        envelope = RawEnvelope(
            dataset=dataset,
            source=source,
            endpoint=endpoint,
            params=dict(params),
            payload=payload,
            ingested_at_ms=ingested_at_ms,
            content_sha256=digest,
        )
        path = self.path_for(dataset, ingested_at_ms)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(envelope.to_json())
            fh.write("\n")
        return envelope

    def path_for(self, dataset: str, ts_ms: int | None = None) -> Path:
        return self.root / validate_dataset_name(dataset) / utc_date_path(ts_ms) / "raw.jsonl"

    def iter_envelopes(self, dataset: str) -> list[RawEnvelope]:
        validate_dataset_name(dataset)
        records: list[RawEnvelope] = []
        for path in sorted((self.root / dataset).glob("year=*/month=*/day=*/raw.jsonl")):
            with path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    records.append(RawEnvelope(**json.loads(line)))
        return records
