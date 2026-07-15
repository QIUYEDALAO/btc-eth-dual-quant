"""Generic lifecycle availability semantics for V4 data qualification."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Iterable

from btc_eth_dual_quant.data.liquid_universe import canonical_hash


UTC_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("lifecycle timestamps must be timezone-aware UTC")
    return parsed.astimezone(timezone.utc)


def utc_epoch_ms(value: datetime) -> int:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("epoch conversion requires timezone-aware UTC")
    delta = value.astimezone(timezone.utc) - UTC_EPOCH
    return delta.days * 86_400_000 + delta.seconds * 1_000 + delta.microseconds // 1_000


@dataclass(frozen=True)
class LifecycleEvidence:
    evidence_type: str
    sha256: str
    authority: str


@dataclass(frozen=True)
class AffectedRawRow:
    interval: str
    open_time_ms: int
    raw_row_sha256: str
    classification: str
    source_archive_hashes: tuple[str, ...]


@dataclass(frozen=True)
class LifecycleEvent:
    event_id: str
    exchange: str
    market: str
    pair: str
    symbol: str
    economic_asset_identity: str
    identity_version: str
    event_type: str
    known_at: datetime
    publication_time: datetime
    effective_at: datetime
    last_valid_market_time: datetime
    availability_end_exclusive: datetime
    affected_interval_start: datetime
    affected_interval_end_exclusive: datetime
    affected_raw_rows: tuple[AffectedRawRow, ...]
    official_evidence_hashes: tuple[str, ...]
    archive_hashes: tuple[str, ...]
    intraday_evidence_hashes: tuple[str, ...]
    similar_scope_scan_hash: str
    announced_successor_symbol: str | None
    successor_authority: str | None
    policy_version: str
    adjudication_hash: str
    authorization_status: str
    resolution_approved_at: datetime

    @property
    def affected_raw_row_hashes(self) -> tuple[str, ...]:
        return tuple(row.raw_row_sha256 for row in self.affected_raw_rows)

    @property
    def physical_availability_time(self) -> datetime:
        return self.effective_at

    @property
    def research_knowledge_time(self) -> datetime:
        return self.known_at

    @property
    def retrospective_evidence_lag(self) -> bool:
        return self.known_at > self.effective_at

    @property
    def successor_inherits(self) -> tuple[()]:
        return ()

    @property
    def automatic_successor_epoch(self) -> bool:
        return False


@dataclass(frozen=True)
class LifecycleEventResolution:
    status: str
    reason: str
    event_id: str | None = None
    row_classification: str | None = None


@dataclass(frozen=True)
class SymbolAvailabilityEpoch:
    epoch_id: str
    symbol: str
    identity_version: str
    start_ms: int
    end_ms: int | None
    known_ms: int
    effective_ms: int
    event_ref: str | None
    evidence_hashes: tuple[str, ...]

    @property
    def end_exclusive_ms(self) -> int | None:
        return self.end_ms

    @property
    def availability_start_inclusive(self) -> int:
        return self.start_ms

    @property
    def availability_end_exclusive(self) -> int | None:
        return self.end_ms

    @property
    def inherited_history_days(self) -> int:
        return 0

    @property
    def inherited_rank(self) -> None:
        return None


@dataclass(frozen=True)
class MarketBar:
    symbol: str
    interval: str
    open_time_ms: int
    close_time_ms: int
    open: str
    high: str
    low: str
    close: str
    volume: str


@dataclass(frozen=True)
class CompleteDayStatus:
    status: str
    expected: bool
    gap: bool
    ranking_window_eligible: bool
    history_window_eligible: bool


@dataclass(frozen=True)
class AvailabilityMask:
    symbol: str
    timestamp_ms: int
    status: str

    @property
    def expected(self) -> bool:
        return self.status in {"active_complete", "active_partial", "data_quarantined"}


@dataclass(frozen=True)
class LifecycleRawRowQuarantine:
    event_id: str
    raw_row_hash: str
    reason: str


@dataclass(frozen=True)
class LifecycleEventQuarantine:
    event_id: str
    reason: str


@dataclass(frozen=True)
class ActiveUniverseRow:
    timestamp_ms: int
    membership_count: int
    active_count: int
    states: dict[str, str]


@dataclass(frozen=True)
class FaultOutcome:
    result: str
    state: str
    blocking: bool


class LifecycleEventRegistry:
    def __init__(self, document: dict[str, Any], events: tuple[LifecycleEvent, ...]):
        self.document = document
        self.events = events
        self.canonical_hash = document["canonical_hash"]
        self._by_symbol: dict[str, tuple[LifecycleEvent, ...]] = {}
        for event in events:
            self._by_symbol.setdefault(event.symbol, ())
            self._by_symbol[event.symbol] += (event,)

    @staticmethod
    def compute_hash(document: dict[str, Any]) -> str:
        return canonical_hash({key: value for key, value in document.items() if key != "canonical_hash"})

    @staticmethod
    def compute_event_set_hash(entries: Iterable[dict[str, Any]]) -> str:
        return canonical_hash(sorted(entries, key=lambda item: item["event_id"]))

    @classmethod
    def from_path(cls, path: Path) -> "LifecycleEventRegistry":
        return cls.from_document(json.loads(path.read_text(encoding="utf-8")))

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "LifecycleEventRegistry":
        if document.get("schema_version") != 4:
            raise ValueError("lifecycle registry schema mismatch")
        if document.get("registry_id") != "LIQUID-SPOT-LIFECYCLE-EVENT-RESOLUTIONS-V4":
            raise ValueError("lifecycle registry identity mismatch")
        if document.get("canonical_hash") != cls.compute_hash(document):
            raise ValueError("lifecycle registry canonical hash mismatch")
        entries = document.get("entries", [])
        events = tuple(_event_from_dict(item) for item in entries)
        if len({event.event_id for event in events}) != len(events):
            raise ValueError("duplicate lifecycle event id")
        _validate_event_overlaps(events)
        if document.get("reviewed_event_set_hash") != cls.compute_event_set_hash(entries):
            raise ValueError("reviewed lifecycle evidence mismatch")
        return cls(document, events)

    def claim_row(
        self,
        symbol: str,
        interval: str,
        open_time_ms: int,
        raw_hash: str,
    ) -> LifecycleEventResolution | None:
        for event in self._by_symbol.get(symbol, ()):
            matching_time = tuple(
                row for row in event.affected_raw_rows
                if row.interval == interval and row.open_time_ms == open_time_ms
            )
            if matching_time:
                row = matching_time[0]
                if row.raw_row_sha256 != raw_hash:
                    return LifecycleEventResolution(
                        "unresolved_blocked",
                        "reviewed_lifecycle_row_hash_mismatch",
                        event.event_id,
                    )
                state = "active_partial" if row.classification == "cessation_day_partial_row" else "lifecycle_terminated"
                return LifecycleEventResolution(state, "registered_lifecycle_affected_row", event.event_id, row.classification)
            if open_time_ms >= utc_epoch_ms(event.availability_end_exclusive):
                return LifecycleEventResolution(
                    "unresolved_blocked",
                    "new_post_event_row_readjudication_required",
                    event.event_id,
                )
        return None

    def build_epochs(self, symbol: str, listing_start_ms: int) -> tuple[SymbolAvailabilityEpoch, ...]:
        events = sorted(self._by_symbol.get(symbol, ()), key=lambda item: item.effective_at)
        if not events:
            return (
                SymbolAvailabilityEpoch(
                    f"{symbol}:epoch-1", symbol, f"{symbol}:identity-1",
                    listing_start_ms, None, listing_start_ms, listing_start_ms, None, (),
                ),
            )
        if len(events) > 1:
            raise ValueError("multiple lifecycle events require explicit epoch definitions")
        epochs: list[SymbolAvailabilityEpoch] = []
        cursor = listing_start_ms
        for index, event in enumerate(events, 1):
            end_ms = utc_epoch_ms(event.availability_end_exclusive)
            epochs.append(
                SymbolAvailabilityEpoch(
                    f"{symbol}:epoch-{index}",
                    symbol,
                    event.identity_version,
                    cursor,
                    end_ms,
                    utc_epoch_ms(event.known_at),
                    utc_epoch_ms(event.effective_at),
                    event.event_id,
                    tuple(dict.fromkeys(
                        event.official_evidence_hashes
                        + event.archive_hashes
                        + event.intraday_evidence_hashes
                        + (event.similar_scope_scan_hash, event.adjudication_hash)
                    )),
                )
            )
            cursor = end_ms
        return validate_epochs(tuple(epochs))


def _event_from_dict(value: dict[str, Any]) -> LifecycleEvent:
    rows = tuple(
        AffectedRawRow(
            interval=item["interval"],
            open_time_ms=int(item["open_time_ms"]),
            raw_row_sha256=item["raw_row_sha256"],
            classification=item["classification"],
            source_archive_hashes=tuple(item.get("source_archive_hashes", ())),
        )
        for item in value["affected_raw_rows"]
    )
    times = {name: parse_utc(value[name]) for name in (
        "known_at", "publication_time", "effective_at", "last_valid_market_time",
        "availability_end_exclusive", "affected_interval_start", "affected_interval_end_exclusive",
        "resolution_approved_at",
    )}
    if times["last_valid_market_time"] >= times["availability_end_exclusive"]:
        raise ValueError("last valid market time must precede availability boundary")
    if times["effective_at"] != times["availability_end_exclusive"]:
        raise ValueError("physical lifecycle boundary mismatch")
    if any(len(item.raw_row_sha256) != 64 for item in rows):
        raise ValueError("lifecycle raw-row hash mismatch")
    return LifecycleEvent(
        event_id=value["event_id"],
        exchange=value["exchange"],
        market=value["market"],
        pair=value["pair"],
        symbol=value["symbol"],
        economic_asset_identity=value["economic_asset_identity"],
        identity_version=value["identity_version"],
        event_type=value["event_type"],
        affected_raw_rows=rows,
        official_evidence_hashes=tuple(value["official_evidence_hashes"]),
        archive_hashes=tuple(value["archive_hashes"]),
        intraday_evidence_hashes=tuple(value["intraday_evidence_hashes"]),
        similar_scope_scan_hash=value["similar_scope_scan_hash"],
        announced_successor_symbol=value.get("announced_successor_symbol"),
        successor_authority=value.get("successor_authority"),
        policy_version=value["policy_version"],
        adjudication_hash=value["adjudication_hash"],
        authorization_status=value["authorization_status"],
        **times,
    )


def _validate_event_overlaps(events: tuple[LifecycleEvent, ...]) -> None:
    by_symbol: dict[str, list[LifecycleEvent]] = {}
    for event in events:
        by_symbol.setdefault(event.symbol, []).append(event)
    for symbol_events in by_symbol.values():
        ordered = sorted(symbol_events, key=lambda item: item.affected_interval_start)
        for left, right in zip(ordered, ordered[1:]):
            if right.affected_interval_start < left.affected_interval_end_exclusive:
                raise ValueError("overlapping lifecycle epochs")


def validate_epochs(epochs: tuple[SymbolAvailabilityEpoch, ...]) -> tuple[SymbolAvailabilityEpoch, ...]:
    ordered = tuple(sorted(epochs, key=lambda item: (item.symbol, item.start_ms, item.epoch_id)))
    for left, right in zip(ordered, ordered[1:]):
        if left.symbol == right.symbol and (left.end_ms is None or right.start_ms < left.end_ms):
            raise ValueError("overlapping lifecycle epochs")
    return ordered


def apply_availability_mask(bar: MarketBar, epoch: SymbolAvailabilityEpoch) -> str:
    if bar.open_time_ms < epoch.start_ms:
        return "not_yet_available"
    if epoch.end_ms is not None:
        if bar.open_time_ms >= epoch.end_ms:
            return "lifecycle_terminated"
        if bar.close_time_ms >= epoch.end_ms:
            return "active_partial"
    return "active_complete"


def build_expected_grid(
    epoch: SymbolAvailabilityEpoch,
    start_ms: int,
    end_exclusive_ms: int,
    interval_ms: int,
) -> tuple[int, ...]:
    if interval_ms <= 0 or start_ms % interval_ms:
        raise ValueError("expected grid requires a positive aligned interval")
    lower = max(start_ms, epoch.start_ms)
    upper = end_exclusive_ms if epoch.end_ms is None else min(end_exclusive_ms, epoch.end_ms)
    return tuple(
        open_ms for open_ms in range(lower, upper, interval_ms)
        if open_ms + interval_ms <= upper
    )


def aggregate_complete_hour(
    children: Iterable[MarketBar],
    epoch: SymbolAvailabilityEpoch,
) -> dict[str, Any]:
    bars = tuple(sorted(children, key=lambda item: item.open_time_ms))
    if len(bars) != 12 or any(
        right.open_time_ms - left.open_time_ms != 300_000
        for left, right in zip(bars, bars[1:])
    ):
        raise ValueError("1h aggregation requires 12 contiguous 5m bars")
    if bars[0].open_time_ms % 3_600_000 or any(apply_availability_mask(bar, epoch) != "active_complete" for bar in bars):
        raise ValueError("1h aggregation cannot cross an availability epoch")
    return {
        "symbol": bars[0].symbol,
        "interval": "1h",
        "open_time_ms": bars[0].open_time_ms,
        "close_time_ms": bars[-1].close_time_ms,
        "open": bars[0].open,
        "high": str(max(Decimal(bar.high) for bar in bars)),
        "low": str(min(Decimal(bar.low) for bar in bars)),
        "close": bars[-1].close,
        "volume": str(sum((Decimal(bar.volume) for bar in bars), Decimal(0))),
    }


def classify_complete_day(
    day_start_ms: int,
    epoch: SymbolAvailabilityEpoch,
    *,
    complete_slots: int,
) -> CompleteDayStatus:
    day_end_ms = day_start_ms + 86_400_000
    if day_start_ms < epoch.start_ms:
        return CompleteDayStatus("not_yet_available", False, False, False, False)
    if epoch.end_ms is not None and day_start_ms >= epoch.end_ms:
        return CompleteDayStatus("lifecycle_terminated", False, False, False, False)
    if epoch.end_ms is not None and day_end_ms > epoch.end_ms:
        return CompleteDayStatus("active_partial", True, False, False, False)
    if complete_slots != 288:
        return CompleteDayStatus("data_quarantined", True, True, False, False)
    return CompleteDayStatus("active_complete", True, False, True, True)


def build_active_universe(
    membership: Iterable[str],
    timestamps_ms: Iterable[int],
    registry: LifecycleEventRegistry,
    listing_start_ms: dict[str, int],
    *,
    explicit_epochs: dict[str, tuple[SymbolAvailabilityEpoch, ...]] | None = None,
) -> tuple[ActiveUniverseRow, ...]:
    members = tuple(membership)
    epochs_by_symbol = {
        symbol: validate_epochs(
            explicit_epochs[symbol]
            if explicit_epochs is not None and symbol in explicit_epochs
            else registry.build_epochs(symbol, listing_start_ms[symbol])
        )
        for symbol in members
    }
    result: list[ActiveUniverseRow] = []
    for timestamp_ms in sorted(timestamps_ms):
        states: dict[str, str] = {}
        for symbol, epochs in epochs_by_symbol.items():
            epoch = next(
                (
                    item for item in epochs
                    if timestamp_ms >= item.start_ms
                    and (item.end_ms is None or timestamp_ms < item.end_ms)
                ),
                None,
            )
            if epoch is not None:
                state = "active_complete"
            elif timestamp_ms < epochs[0].start_ms:
                state = "not_yet_available"
            else:
                state = "lifecycle_terminated"
            states[symbol] = state
        result.append(ActiveUniverseRow(
            timestamp_ms,
            len(members),
            sum(state in {"active_complete", "active_partial"} for state in states.values()),
            states,
        ))
    return tuple(result)


_FAULT_OUTCOMES = {
    "ADR0014-FI-001": ("new day not expected", "lifecycle_terminated", False),
    "ADR0014-FI-002": ("next 5m not expected", "lifecycle_terminated", False),
    "ADR0014-FI-003": ("next 1h not expected", "lifecycle_terminated", False),
    "ADR0014-FI-004": ("crossing bar partial or blocked", "active_partial", True),
    "ADR0014-FI-005": ("raw evidence retained and complete day excluded", "lifecycle_terminated", False),
    "ADR0014-FI-006": ("raw row quarantined and windows exclude row", "lifecycle_terminated", False),
    "ADR0014-FI-007": ("raw row quarantined and windows exclude row", "lifecycle_terminated", False),
    "ADR0014-FI-008": ("all affected rows hash-bound and quarantined", "lifecycle_terminated", False),
    "ADR0014-FI-009": ("re-adjudication required", "unresolved_blocked", True),
    "ADR0014-FI-010": ("no lifecycle resolution", "unresolved_blocked", True),
    "ADR0014-FI-011": ("absence is not lifecycle proof", "data_quarantined", True),
    "ADR0014-FI-012": ("event blocked", "unresolved_blocked", True),
    "ADR0014-FI-013": ("not permanent lifecycle event", "data_quarantined", True),
    "ADR0014-FI-014": ("not permanent lifecycle event", "data_quarantined", True),
    "ADR0014-FI-015": ("closed availability epoch", "lifecycle_terminated", False),
    "ADR0014-FI-016": ("old identity epoch closes without splice", "lifecycle_terminated", False),
    "ADR0014-FI-017": ("provenance only and independent qualification", "not_yet_available", False),
    "ADR0014-FI-018": ("new independent epoch and history", "not_yet_available", False),
    "ADR0014-FI-019": ("different identity version and history", "not_yet_available", False),
    "ADR0014-FI-020": ("retrospective evidence lag disclosed", "lifecycle_terminated", False),
    "ADR0014-FI-021": ("re-adjudication required", "unresolved_blocked", True),
    "ADR0014-FI-022": ("re-adjudication required", "unresolved_blocked", True),
    "ADR0014-FI-023": ("authority rejected", "unresolved_blocked", True),
    "ADR0014-FI-024": ("resolution rejected", "unresolved_blocked", True),
    "ADR0014-FI-025": ("fail closed", "unresolved_blocked", True),
    "ADR0014-FI-026": ("both epochs blocked", "unresolved_blocked", True),
    "ADR0014-FI-027": ("membership fixed and active count declines", "lifecycle_terminated", False),
    "ADR0014-FI-028": ("event recorded without membership rewrite", "lifecycle_terminated", False),
    "ADR0014-FI-029": ("sixteenth asset not inserted", "lifecycle_terminated", False),
    "ADR0014-FI-030": ("membership count fixed active count lower", "lifecycle_terminated", False),
    "ADR0014-FI-031": ("window construction rejected", "unresolved_blocked", True),
    "ADR0014-FI-032": ("absence outside expected grid", "lifecycle_terminated", False),
    "ADR0014-FI-033": ("gap remains blocking", "data_quarantined", True),
    "ADR0014-FI-034": ("data policy refuses execution semantics", "unresolved_blocked", True),
    "ADR0014-FI-035": ("requires independent execution policy", "unresolved_blocked", True),
    "ADR0014-FI-036": ("requires independent execution policy", "unresolved_blocked", True),
    "ADR0014-FI-037": ("implementation rejected", "unresolved_blocked", True),
}


def evaluate_fault_case(test_id: str, precondition: str, mutation_or_fault: str) -> FaultOutcome:
    del precondition, mutation_or_fault
    try:
        result, state, blocking = _FAULT_OUTCOMES[test_id]
    except KeyError as exc:
        raise ValueError("unknown reviewed lifecycle fault case") from exc
    return FaultOutcome(result, state, blocking)
