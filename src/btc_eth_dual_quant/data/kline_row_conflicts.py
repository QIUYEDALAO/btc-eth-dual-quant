"""Generic, deterministic kline row-conflict semantics for V3 qualification."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any, Iterable

from btc_eth_dual_quant.data.liquid_universe import canonical_hash

KLINE_FIELDS = (
    "open_time", "open", "high", "low", "close", "base_volume",
    "close_time", "quote_volume", "trade_count", "taker_buy_base_volume",
    "taker_buy_quote_volume", "ignore",
)
DECIMAL_INDEXES = (1, 2, 3, 4, 5, 7, 9, 10)
VOLUME_INDEXES = (5, 7, 9, 10)
EXPECTED_ADJUDICATION_HASH = "8214079900d311c232ecde4b348712f2a5a6d958c8cd98270b9501a71f77330b"
ALLOWED_ACTIONS = {
    "collapse_byte_identical_duplicate",
    "replace_invalid_monthly_with_daily",
}


def timestamp_ms(value: str) -> int:
    if not value.isdigit():
        raise ValueError("kline timestamp must be an unsigned integer")
    raw = int(value)
    return raw // 1_000 if raw >= 10**15 else raw


def normalize_kline_fields(fields: Iterable[str]) -> tuple[Any, ...]:
    values = tuple(fields)
    if len(values) != 12:
        raise ValueError("kline row must contain exactly 12 fields")
    normalized: list[Any] = []
    for index, value in enumerate(values):
        if index in (0, 6):
            normalized.append(timestamp_ms(value))
        elif index in DECIMAL_INDEXES:
            try:
                decimal = Decimal(value)
            except InvalidOperation as exc:
                raise ValueError(f"invalid decimal field: {KLINE_FIELDS[index]}") from exc
            if not decimal.is_finite():
                raise ValueError(f"non-finite field: {KLINE_FIELDS[index]}")
            normalized.append(decimal)
        elif index == 8:
            if not value.isdigit():
                raise ValueError("trade_count must be a non-negative integer")
            normalized.append(int(value))
        else:
            normalized.append(value)
    return tuple(normalized)


def structural_errors(fields: Iterable[str], *, interval: str) -> tuple[str, ...]:
    try:
        values = normalize_kline_fields(fields)
    except ValueError as exc:
        return (str(exc),)
    errors: list[str] = []
    open_time, open_, high, low, close, _, close_time, *_ = values
    step_ms = {"1d": 86_400_000, "5m": 300_000}.get(interval)
    if step_ms is None:
        errors.append("unsupported interval")
    else:
        if open_time % step_ms:
            errors.append("off-grid open_time")
        interval_end = open_time + step_ms - 1
        if interval == "1d":
            if not open_time <= close_time <= interval_end:
                errors.append("close_time outside interval")
        elif close_time != interval_end:
            errors.append("invalid close_time")
    if low > min(open_, close) or high < max(open_, close) or low > high:
        errors.append("invalid OHLC ordering")
    for index in VOLUME_INDEXES:
        if values[index] < 0:
            errors.append(f"negative {KLINE_FIELDS[index]}")
    return tuple(errors)


@dataclass(frozen=True)
class RawKlineRow:
    symbol: str
    interval: str
    fields: tuple[str, ...]
    line_number: int
    archive_key: str
    archive_sha256: str
    authority: str

    @classmethod
    def from_fields(
        cls,
        *,
        symbol: str,
        interval: str,
        fields: Iterable[str],
        line_number: int,
        archive_key: str,
        archive_sha256: str,
        authority: str,
    ) -> "RawKlineRow":
        values = tuple(fields)
        if len(values) != 12:
            raise ValueError("kline row must contain exactly 12 fields")
        if line_number < 1:
            raise ValueError("line number must be positive")
        if len(archive_sha256) != 64:
            raise ValueError("archive SHA256 must contain 64 characters")
        return cls(symbol, interval, values, line_number, archive_key, archive_sha256, authority)

    @property
    def canonical_key(self) -> tuple[str, str, int]:
        return self.symbol, self.interval, timestamp_ms(self.fields[0])

    @property
    def open_time_utc(self) -> str:
        return datetime.fromtimestamp(self.canonical_key[2] / 1_000, timezone.utc).isoformat()

    @property
    def raw_row_hash(self) -> str:
        return canonical_hash(list(self.fields))

    @property
    def normalized(self) -> tuple[Any, ...]:
        return normalize_kline_fields(self.fields)

    @property
    def errors(self) -> tuple[str, ...]:
        return structural_errors(self.fields, interval=self.interval)


@dataclass(frozen=True)
class CompleteGroup:
    key: tuple[str, str, int]
    classification: str
    raw_multiplicity: int
    raw_row_hashes: tuple[str, ...]
    line_numbers: tuple[int, ...]
    collapsible: bool


def classify_complete_group(rows: Iterable[RawKlineRow]) -> CompleteGroup:
    members = tuple(rows)
    if not members:
        raise ValueError("complete group cannot be empty")
    keys = {row.canonical_key for row in members}
    if len(keys) != 1:
        raise ValueError("complete group contains multiple canonical keys")
    if len(members) == 1:
        classification = "single"
    elif len({row.fields[0] for row in members}) > 1:
        classification = "parser_created_duplicate"
    elif all(row.fields == members[0].fields for row in members[1:]):
        classification = "byte_identical_duplicate"
    elif all(row.normalized == members[0].normalized for row in members[1:]):
        classification = "semantic_identical_duplicate"
    else:
        classification = "conflicting_duplicate"
    return CompleteGroup(
        key=members[0].canonical_key,
        classification=classification,
        raw_multiplicity=len(members),
        raw_row_hashes=tuple(row.raw_row_hash for row in members),
        line_numbers=tuple(row.line_number for row in members),
        collapsible=classification in {"single", "byte_identical_duplicate"},
    )


@dataclass(frozen=True)
class ArchiveEvidence:
    canonical_key: str
    sha256: str
    raw_row_hashes: tuple[str, ...]
    raw_rows: tuple[tuple[str, ...], ...]
    raw_multiplicity: int


@dataclass(frozen=True)
class RestComparator:
    endpoint_identity: str
    payload_sha256: str
    normalized_rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ResolutionEntry:
    resolution_id: str
    conflict_id: str
    symbol: str
    interval: str
    open_time_utc: str
    conflict_class: str
    monthly_archive: ArchiveEvidence
    daily_archive: ArchiveEvidence
    rest_comparators: tuple[RestComparator, ...]
    adjudication_evidence_hash: str
    approved_action: str
    invalid_fields: tuple[str, ...]
    policy_version: str
    effective_contract_version: str

    @property
    def key(self) -> tuple[str, str, int]:
        return self.symbol, self.interval, int(datetime.fromisoformat(self.open_time_utc).timestamp() * 1_000)

    def as_dict(self) -> dict[str, Any]:
        return {
            "resolution_id": self.resolution_id,
            "conflict_id": self.conflict_id,
            "symbol": self.symbol,
            "interval": self.interval,
            "open_time_utc": self.open_time_utc,
            "conflict_class": self.conflict_class,
            "monthly_archive": _archive_as_dict(self.monthly_archive),
            "daily_archive": _archive_as_dict(self.daily_archive),
            "rest_comparators": [
                {
                    "endpoint_identity": item.endpoint_identity,
                    "payload_sha256": item.payload_sha256,
                    "normalized_rows": [list(row) for row in item.normalized_rows],
                }
                for item in self.rest_comparators
            ],
            "adjudication_evidence_hash": self.adjudication_evidence_hash,
            "approved_action": self.approved_action,
            "invalid_fields": list(self.invalid_fields),
            "policy_version": self.policy_version,
            "effective_contract_version": self.effective_contract_version,
        }


def _archive_as_dict(item: ArchiveEvidence) -> dict[str, Any]:
    return {
        "canonical_key": item.canonical_key,
        "sha256": item.sha256,
        "raw_row_hashes": list(item.raw_row_hashes),
        "raw_rows": [list(row) for row in item.raw_rows],
        "raw_multiplicity": item.raw_multiplicity,
    }


class ResolutionRegistry:
    def __init__(self, document: dict[str, Any], entries: tuple[ResolutionEntry, ...]):
        self.document = document
        self.entries = entries
        self.adjudication_evidence_hash = document["adjudication_evidence_hash"]
        self.canonical_hash = document["canonical_hash"]
        self._by_key = {entry.key: entry for entry in entries}

    @staticmethod
    def compute_hash(document: dict[str, Any]) -> str:
        return canonical_hash({key: value for key, value in document.items() if key != "canonical_hash"})

    @classmethod
    def from_path(cls, path: Path) -> "ResolutionRegistry":
        return cls.from_document(json.loads(path.read_text(encoding="utf-8")))

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "ResolutionRegistry":
        if document.get("schema_version") != 3 or document.get("registry_id") != "LIQUID-SPOT-SOURCE-CONFLICT-RESOLUTIONS-V3":
            raise ValueError("resolution registry identity mismatch")
        if document.get("canonical_hash") != cls.compute_hash(document):
            raise ValueError("registry canonical hash mismatch")
        if document.get("adjudication_evidence_hash") != EXPECTED_ADJUDICATION_HASH:
            raise ValueError("adjudication evidence hash mismatch")
        entries = tuple(_entry_from_dict(item) for item in document.get("entries", []))
        keys = [entry.key for entry in entries]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate resolution key")
        for entry in entries:
            if entry.adjudication_evidence_hash != document["adjudication_evidence_hash"]:
                raise ValueError("entry adjudication evidence hash mismatch")
            if entry.approved_action not in ALLOWED_ACTIONS:
                raise ValueError("unknown approved resolution action")
            if len(entry.rest_comparators) != 2:
                raise ValueError("every resolution requires two frozen REST comparators")
            for source in (entry.monthly_archive, entry.daily_archive):
                if len(source.sha256) != 64:
                    raise ValueError("source archive SHA256 mismatch")
                if len(source.raw_row_hashes) != source.raw_multiplicity:
                    raise ValueError("source raw multiplicity mismatch")
                if source.raw_rows and (
                    len(source.raw_rows) != source.raw_multiplicity
                    or tuple(canonical_hash(list(row)) for row in source.raw_rows) != source.raw_row_hashes
                ):
                    raise ValueError("source raw-row hash mismatch")
            identities = {item.endpoint_identity for item in entry.rest_comparators}
            if identities != {"api.binance.com", "data-api.binance.vision"}:
                raise ValueError("frozen comparator identity mismatch")
            if any(len(item.payload_sha256) != 64 or len(item.normalized_rows) != 1 for item in entry.rest_comparators):
                raise ValueError("frozen comparator evidence mismatch")
        return cls(document, entries)

    def get(self, key: tuple[str, str, int]) -> ResolutionEntry | None:
        return self._by_key.get(key)


def _archive_from_dict(value: dict[str, Any]) -> ArchiveEvidence:
    return ArchiveEvidence(
        canonical_key=value["canonical_key"],
        sha256=value["sha256"],
        raw_row_hashes=tuple(value["raw_row_hashes"]),
        raw_rows=tuple(tuple(row) for row in value.get("raw_rows", [])),
        raw_multiplicity=int(value["raw_multiplicity"]),
    )


def _entry_from_dict(value: dict[str, Any]) -> ResolutionEntry:
    return ResolutionEntry(
        resolution_id=value["resolution_id"],
        conflict_id=value["conflict_id"],
        symbol=value["symbol"],
        interval=value["interval"],
        open_time_utc=value["open_time_utc"],
        conflict_class=value["conflict_class"],
        monthly_archive=_archive_from_dict(value["monthly_archive"]),
        daily_archive=_archive_from_dict(value["daily_archive"]),
        rest_comparators=tuple(
            RestComparator(
                endpoint_identity=item["endpoint_identity"],
                payload_sha256=item["payload_sha256"],
                normalized_rows=tuple(tuple(row) for row in item["normalized_rows"]),
            )
            for item in value["rest_comparators"]
        ),
        adjudication_evidence_hash=value["adjudication_evidence_hash"],
        approved_action=value["approved_action"],
        invalid_fields=tuple(value["invalid_fields"]),
        policy_version=value["policy_version"],
        effective_contract_version=value["effective_contract_version"],
    )
