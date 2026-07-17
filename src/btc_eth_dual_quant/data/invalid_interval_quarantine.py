"""Generic ADR-0015 synchronized invalid-interval quarantine semantics.

The module preserves physical CSV rows, derives events only from verified
official archives and point-in-time membership, and emits a separate slot
mask.  It contains no known date or symbol exceptions and performs no source
repair, filling, replacement, research, or execution behavior.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import timedelta
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
import zipfile

from btc_eth_dual_quant.data.kline_row_conflicts import normalize_kline_fields
from btc_eth_dual_quant.data.liquid_universe import MinuteBar, canonical_hash
from btc_eth_dual_quant.data.lifecycle_availability import UTC_EPOCH


FIVE_MINUTE_MS = 300_000
VALID_CLOSE_DELTA_MS = 299_999
ADR0015_MANIFEST_TYPES = (
    "invalid_interval_policy_manifest",
    "invalid_interval_event_manifest",
    "invalid_interval_slot_mask_manifest",
    "invalid_interval_accounting_manifest",
)
ADR0015_FAULT_IDS = tuple(f"ADR0015-FI-{index:03d}" for index in range(1, 17))

EXPECTED_AUTHORIZATIONS = {
    "generic_policy_implementation": True,
    "fixture_validation": True,
    "fault_injection": True,
    "exact_head_implementation_review": True,
    "fixed_range_public_requalification": False,
    "new_independent_audit_protocol": False,
    "new_independent_audit": False,
    "u04": False,
    "hypothesis_or_strategy": False,
    "event_scan_signals_or_returns": False,
    "backtesting_or_oos": False,
    "api_or_trading": False,
    "execution_live": False,
    "m2": False,
}
EXPECTED_HARD_BLOCKS = {
    "open_time_off_grid",
    "non_time_field_invalid_or_nonfinite",
    "ohlcv_legality_failure",
    "missing_expected_row",
    "duplicate_row",
    "non_member_row",
    "membership_ambiguity",
    "archive_or_evidence_hash_drift",
    "source_revision",
    "affected_fraction_below_threshold",
    "affected_symbol_count_below_threshold",
    "policy_overlap",
    "order_content_hash_mismatch",
}


class PolicyHardBlock(ValueError):
    """Raised when authority or physical-source identity cannot be trusted."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _strict_timestamp_ms(value: str) -> int:
    if not value or not value.isdigit():
        raise PolicyHardBlock("timestamp is not an unsigned integer")
    raw = int(value)
    if raw >= 10**14:
        raw //= 1_000
    if raw < 10**11 or raw >= 10**14:
        raise PolicyHardBlock("unsupported timestamp unit")
    return raw


def _month_for_ms(value: int) -> str:
    moment = UTC_EPOCH + timedelta(milliseconds=value)
    return f"{moment.year:04d}-{moment.month:02d}"


def _parse_raw_line(raw_line: bytes, line_number: int) -> tuple[str, ...] | None:
    try:
        text = raw_line.decode("utf-8-sig" if line_number == 1 else "utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyHardBlock(f"invalid CSV encoding at line {line_number}") from exc
    records = list(csv.reader(io.StringIO(text)))
    if len(records) != 1:
        raise PolicyHardBlock(f"ambiguous CSV row at line {line_number}")
    fields = tuple(field.strip() for field in records[0])
    if line_number == 1 and fields and not fields[0].isdigit():
        return None
    if len(fields) != 12:
        raise PolicyHardBlock(f"non-12-field kline at line {line_number}")
    return fields


@dataclass(frozen=True)
class InvalidIntervalPolicy:
    document: dict[str, Any]
    canonical_hash: str
    algorithm_hash: str
    policy_version: str
    source_freeze_content_hash: str
    membership_manifest_content_hash: str
    lifecycle_registry_hash: str
    minimum_count: int
    fraction_numerator: int
    fraction_denominator: int

    @classmethod
    def from_path(cls, path: Path) -> "InvalidIntervalPolicy":
        return cls.from_document(json.loads(path.read_text(encoding="utf-8")))

    @classmethod
    def from_document(cls, document: Mapping[str, Any]) -> "InvalidIntervalPolicy":
        value = dict(document)
        if value.get("schema_version") != 1:
            raise PolicyHardBlock("invalid-interval policy schema mismatch")
        if value.get("policy_id") != "LIQUID-SPOT-SYNCHRONIZED-INVALID-INTERVAL-QUARANTINE-V1":
            raise PolicyHardBlock("invalid-interval policy identity mismatch")
        declared_hash = value.get("canonical_hash")
        actual_hash = canonical_hash({key: item for key, item in value.items() if key != "canonical_hash"})
        if declared_hash != actual_hash:
            raise PolicyHardBlock("invalid-interval policy canonical hash mismatch")
        algorithm = value.get("algorithm", {})
        if value.get("algorithm_hash") != canonical_hash(algorithm):
            raise PolicyHardBlock("invalid-interval algorithm hash mismatch")
        market = value.get("market", {})
        if market != {
            "exchange": "binance",
            "market": "spot",
            "interval": "5m",
            "open_time_grid_ms": FIVE_MINUTE_MS,
            "valid_close_delta_ms": VALID_CLOSE_DELTA_MS,
        }:
            raise PolicyHardBlock("invalid-interval market semantics changed")
        threshold = value.get("candidate_threshold", {})
        if threshold != {
            "minimum_invalid_active_members": 2,
            "minimum_fraction_numerator": 4,
            "minimum_fraction_denominator": 5,
            "fraction_denominator": "all_active_members_at_open_time",
        }:
            raise PolicyHardBlock("invalid-interval threshold changed")
        if value.get("authorizations") != EXPECTED_AUTHORIZATIONS:
            raise PolicyHardBlock("invalid-interval authorization matrix changed")
        if set(value.get("hard_block_conditions", ())) != EXPECTED_HARD_BLOCKS:
            raise PolicyHardBlock("invalid-interval hard-block set changed")
        if algorithm.get("known_date_symbol_or_row_exceptions") is not False:
            raise PolicyHardBlock("known date/symbol exceptions are forbidden")
        if algorithm.get("raw_rows_are_rewritten") is not False:
            raise PolicyHardBlock("raw-row rewrite is forbidden")
        if algorithm.get("synthetic_fills") is not False or algorithm.get("replacement_members") is not False:
            raise PolicyHardBlock("fill or replacement authority is forbidden")
        if algorithm.get("direct_v2_gap_policy_reuse") is not False:
            raise PolicyHardBlock("direct V2 gap-policy reuse is forbidden")
        bindings = value.get("bindings", {})
        required_bindings = (
            "adopted_adr_file_sha256",
            "adopted_semantic_body_hash",
            "adoption_content_hash",
            "review_content_hash",
            "protocol_content_hash",
            "diagnostic_content_hash",
            "diagnostic_run_content_hash",
            "source_freeze_content_hash",
            "membership_manifest_content_hash",
            "lifecycle_registry_hash",
            "v2_gap_policy_contract_hash",
        )
        if any(not _is_sha256(bindings.get(name)) for name in required_bindings):
            raise PolicyHardBlock("invalid-interval evidence binding is malformed")
        return cls(
            value,
            declared_hash,
            value["algorithm_hash"],
            value["policy_version"],
            bindings["source_freeze_content_hash"],
            bindings["membership_manifest_content_hash"],
            bindings["lifecycle_registry_hash"],
            threshold["minimum_invalid_active_members"],
            threshold["minimum_fraction_numerator"],
            threshold["minimum_fraction_denominator"],
        )


@dataclass(frozen=True)
class VerifiedFiveMinuteRow:
    symbol: str
    month: str
    open_time_ms: int
    close_time_ms: int
    raw_fields: tuple[str, ...]
    raw_line: bytes
    raw_line_sha256: str
    line_number: int
    archive_key: str
    archive_sha256: str
    archive_byte_size: int
    member_name: str
    source_freeze_content_hash: str

    @property
    def normalized(self) -> tuple[Any, ...]:
        return normalize_kline_fields(self.raw_fields)

    @property
    def valid_close_boundary(self) -> bool:
        return self.close_time_ms == self.open_time_ms + VALID_CLOSE_DELTA_MS

    def identity_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if _sha256(self.raw_line) != self.raw_line_sha256:
            errors.append("raw_row_hash_drift")
        try:
            reparsed = _parse_raw_line(self.raw_line, self.line_number)
        except PolicyHardBlock:
            reparsed = None
        if reparsed != self.raw_fields:
            errors.append("raw_row_content_drift")
        try:
            raw_open = _strict_timestamp_ms(self.raw_fields[0])
            raw_close = _strict_timestamp_ms(self.raw_fields[6])
        except PolicyHardBlock:
            errors.append("timestamp_malformed")
        else:
            if raw_open != self.open_time_ms or raw_close != self.close_time_ms:
                errors.append("raw_timestamp_repaired")
        if _month_for_ms(self.open_time_ms) != self.month:
            errors.append("timestamp_outside_archive_month")
        return tuple(sorted(set(errors)))

    def structural_errors(self) -> tuple[str, ...]:
        errors: list[str] = list(self.identity_errors())
        try:
            values = self.normalized
        except ValueError:
            return tuple(sorted(set(errors + ["non_time_field_invalid_or_nonfinite"])))
        _, open_, high, low, close, volume, _, quote_volume, trades, taker_base, taker_quote, _ = values
        if self.open_time_ms % FIVE_MINUTE_MS:
            errors.append("open_time_off_grid")
        if low > min(open_, close) or high < max(open_, close) or low > high:
            errors.append("ohlcv_legality_failure")
        if any(item < Decimal(0) for item in (volume, quote_volume, taker_base, taker_quote)):
            errors.append("ohlcv_legality_failure")
        if not isinstance(trades, int) or trades < 0:
            errors.append("non_time_field_invalid_or_nonfinite")
        return tuple(sorted(set(errors)))

    def to_minute_bar(self) -> MinuteBar:
        if self.structural_errors() or not self.valid_close_boundary:
            raise PolicyHardBlock("only strict unmasked 5m rows can become MinuteBar values")
        values = self.normalized
        _, open_, high, low, close, volume, _, quote_volume, trades, taker_base, taker_quote, _ = values
        return MinuteBar(
            symbol=self.symbol,
            open_time=UTC_EPOCH + timedelta(milliseconds=self.open_time_ms),
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            quote_volume=quote_volume,
            trade_count=trades,
            taker_base_volume=taker_base,
            taker_quote_volume=taker_quote,
        )


def read_verified_monthly_five_minute_archive(
    path: Path,
    *,
    binding: Mapping[str, Any],
    symbol: str,
    month: str,
    source_freeze_content_hash: str,
) -> tuple[VerifiedFiveMinuteRow, ...]:
    """Verify one frozen official ZIP and retain exact physical CSV rows."""
    if not _is_sha256(source_freeze_content_hash):
        raise PolicyHardBlock("source-freeze hash is malformed")
    payload = path.read_bytes()
    archive_sha256 = _sha256(payload)
    if archive_sha256 != binding.get("sha256") or len(payload) != binding.get("byte_size"):
        raise PolicyHardBlock("archive_or_evidence_hash_drift")
    archive_key = str(binding.get("canonical_key", ""))
    expected_suffix = f"/{symbol}/5m/{symbol}-5m-{month}.zip"
    if not archive_key.endswith(expected_suffix):
        raise PolicyHardBlock("archive identity mismatch")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
            if len(members) != 1:
                raise PolicyHardBlock("archive member count mismatch")
            member = members[0]
            expected_member = f"{symbol}-5m-{month}.csv"
            if PurePosixPath(member.filename).name != expected_member:
                raise PolicyHardBlock("archive member identity mismatch")
            if archive.testzip() is not None:
                raise PolicyHardBlock("archive CRC failure")
            member_payload = archive.read(member)
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise PolicyHardBlock("archive ZIP/CRC failure") from exc

    rows: list[VerifiedFiveMinuteRow] = []
    for line_number, raw_line in enumerate(member_payload.splitlines(), start=1):
        fields = _parse_raw_line(raw_line, line_number)
        if fields is None:
            continue
        open_time_ms = _strict_timestamp_ms(fields[0])
        close_time_ms = _strict_timestamp_ms(fields[6])
        row = VerifiedFiveMinuteRow(
            symbol=symbol,
            month=month,
            open_time_ms=open_time_ms,
            close_time_ms=close_time_ms,
            raw_fields=fields,
            raw_line=raw_line,
            raw_line_sha256=_sha256(raw_line),
            line_number=line_number,
            archive_key=archive_key,
            archive_sha256=archive_sha256,
            archive_byte_size=len(payload),
            member_name=member.filename,
            source_freeze_content_hash=source_freeze_content_hash,
        )
        rows.append(row)
    return tuple(rows)


@dataclass(frozen=True)
class ActiveMembershipAuthority:
    members_by_month: dict[str, tuple[str, ...]]
    lifecycle_end_exclusive_ms: dict[str, int]
    membership_manifest_content_hash: str
    lifecycle_registry_hash: str
    authority_hash: str

    @classmethod
    def build(
        cls,
        membership_rows: Iterable[Mapping[str, Any]],
        *,
        membership_manifest_content_hash: str,
        lifecycle_registry_hash: str,
        lifecycle_end_exclusive_ms: Mapping[str, int] | None = None,
    ) -> "ActiveMembershipAuthority":
        if not _is_sha256(membership_manifest_content_hash) or not _is_sha256(lifecycle_registry_hash):
            raise PolicyHardBlock("membership authority hash is malformed")
        grouped: dict[str, list[tuple[int, str]]] = {}
        for row in membership_rows:
            month = str(row.get("effective_month", ""))[:7]
            symbol = str(row.get("symbol", ""))
            rank = int(row.get("rank", 0))
            if len(month) != 7 or not symbol or rank < 1:
                raise PolicyHardBlock("membership_ambiguity")
            grouped.setdefault(month, []).append((rank, symbol))
        members: dict[str, tuple[str, ...]] = {}
        for month, rows in grouped.items():
            if len({rank for rank, _ in rows}) != len(rows) or len({symbol for _, symbol in rows}) != len(rows):
                raise PolicyHardBlock("membership_ambiguity")
            members[month] = tuple(symbol for _, symbol in sorted(rows))
            if not members[month]:
                raise PolicyHardBlock("membership_ambiguity")
        endings = {str(symbol): int(value) for symbol, value in (lifecycle_end_exclusive_ms or {}).items()}
        identity = {
            "membership_manifest_content_hash": membership_manifest_content_hash,
            "lifecycle_registry_hash": lifecycle_registry_hash,
            "active_member_rule": "month_start_membership_minus_end_exclusive_lifecycle_termination",
        }
        return cls(members, endings, membership_manifest_content_hash, lifecycle_registry_hash, canonical_hash(identity))

    def active_members_at(self, open_time_ms: int) -> tuple[str, ...]:
        month = _month_for_ms(open_time_ms)
        try:
            members = self.members_by_month[month]
        except KeyError as exc:
            raise PolicyHardBlock("membership_ambiguity") from exc
        active = tuple(
            symbol for symbol in members
            if symbol not in self.lifecycle_end_exclusive_ms
            or open_time_ms < self.lifecycle_end_exclusive_ms[symbol]
        )
        if not active:
            raise PolicyHardBlock("membership_ambiguity")
        return active


@dataclass(frozen=True)
class PolicyBlocker:
    reason: str
    open_time_ms: int | None
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class InvalidIntervalEvent:
    event_id: str
    open_time_ms: int
    active_members: tuple[str, ...]
    invalid_members: tuple[str, ...]
    valid_minority_members: tuple[str, ...]
    invalid_count: int
    valid_minority_count: int
    total_quarantined_count: int
    raw_row_hashes: tuple[str, ...]
    source_archive_hashes: tuple[str, ...]
    membership_authority_hash: str
    source_freeze_content_hash: str
    policy_version: str
    algorithm_hash: str


@dataclass(frozen=True)
class SlotMaskEntry:
    event_id: str
    symbol: str
    month: str
    open_time_ms: int
    classification: str
    raw_row_sha256: str
    archive_sha256: str


@dataclass(frozen=True)
class PolicyEvaluation:
    events: tuple[InvalidIntervalEvent, ...]
    masks: tuple[SlotMaskEntry, ...]
    blockers: tuple[PolicyBlocker, ...]
    accounting: dict[str, Any]

    def canonical_content(self) -> dict[str, Any]:
        return {
            "events": [asdict(item) for item in self.events],
            "masks": [asdict(item) for item in self.masks],
            "blockers": [asdict(item) for item in self.blockers],
            "accounting": self.accounting,
        }

    @property
    def content_hash(self) -> str:
        return canonical_hash(self.canonical_content())


def evaluate_invalid_interval_policy(
    rows: Iterable[VerifiedFiveMinuteRow],
    *,
    policy: InvalidIntervalPolicy,
    membership: ActiveMembershipAuthority,
    existing_policy_claims: Iterable[tuple[str, int]] = (),
) -> PolicyEvaluation:
    """Evaluate generic synchronized events in canonical, input-order-free form."""
    if membership.membership_manifest_content_hash != policy.membership_manifest_content_hash:
        raise PolicyHardBlock("membership_hash_drift")
    if membership.lifecycle_registry_hash != policy.lifecycle_registry_hash:
        raise PolicyHardBlock("membership_hash_drift")
    claims = set(existing_policy_claims)
    members = tuple(rows)
    grouped: dict[int, list[VerifiedFiveMinuteRow]] = {}
    blockers: list[PolicyBlocker] = []
    invalid_candidate_times: set[int] = set()
    structurally_blocked_times: set[int] = set()
    for row in members:
        if row.source_freeze_content_hash != policy.source_freeze_content_hash:
            raise PolicyHardBlock("archive_or_evidence_hash_drift")
        grouped.setdefault(row.open_time_ms, []).append(row)
        structural = row.structural_errors()
        if structural:
            blockers.append(PolicyBlocker(structural[0], row.open_time_ms, (row.symbol,)))
            structurally_blocked_times.add(row.open_time_ms)
        elif not row.valid_close_boundary:
            invalid_candidate_times.add(row.open_time_ms)

    events: list[InvalidIntervalEvent] = []
    masks: list[SlotMaskEntry] = []
    for open_time_ms in sorted(invalid_candidate_times):
        records = sorted(grouped[open_time_ms], key=lambda item: (item.symbol, item.archive_key, item.line_number))
        if open_time_ms in structurally_blocked_times:
            continue
        active = membership.active_members_at(open_time_ms)
        active_set = set(active)
        by_symbol: dict[str, list[VerifiedFiveMinuteRow]] = {}
        for row in records:
            by_symbol.setdefault(row.symbol, []).append(row)
        duplicate = tuple(sorted(symbol for symbol, values in by_symbol.items() if len(values) != 1 and symbol in active_set))
        if duplicate:
            blockers.append(PolicyBlocker("duplicate_row", open_time_ms, duplicate))
            continue
        non_member_invalid = tuple(sorted(
            row.symbol for row in records
            if row.symbol not in active_set and not row.valid_close_boundary
        ))
        if non_member_invalid:
            blockers.append(PolicyBlocker("non_member_row", open_time_ms, non_member_invalid))
            continue
        missing = tuple(sorted(active_set - set(by_symbol)))
        if missing:
            blockers.append(PolicyBlocker("missing_expected_row", open_time_ms, missing))
            continue
        overlap = tuple(sorted(symbol for symbol in active if (symbol, open_time_ms) in claims or ("*", open_time_ms) in claims))
        if overlap:
            blockers.append(PolicyBlocker("policy_overlap", open_time_ms, overlap))
            continue
        selected = {symbol: by_symbol[symbol][0] for symbol in active}
        invalid = tuple(sorted(symbol for symbol, row in selected.items() if not row.valid_close_boundary))
        if len(invalid) < policy.minimum_count:
            blockers.append(PolicyBlocker("affected_symbol_count_below_threshold", open_time_ms, invalid))
            continue
        if len(invalid) * policy.fraction_denominator < len(active) * policy.fraction_numerator:
            blockers.append(PolicyBlocker("affected_fraction_below_threshold", open_time_ms, invalid))
            continue
        valid_minority = tuple(sorted(active_set - set(invalid)))
        identity = {
            "source_freeze_content_hash": policy.source_freeze_content_hash,
            "membership_authority_hash": membership.authority_hash,
            "policy_version": policy.policy_version,
            "algorithm_hash": policy.algorithm_hash,
            "open_time_ms": open_time_ms,
        }
        event_id = canonical_hash(identity)
        active_sorted = tuple(sorted(active))
        event = InvalidIntervalEvent(
            event_id=event_id,
            open_time_ms=open_time_ms,
            active_members=active_sorted,
            invalid_members=invalid,
            valid_minority_members=valid_minority,
            invalid_count=len(invalid),
            valid_minority_count=len(valid_minority),
            total_quarantined_count=len(active_sorted),
            raw_row_hashes=tuple(selected[symbol].raw_line_sha256 for symbol in active_sorted),
            source_archive_hashes=tuple(sorted({selected[symbol].archive_sha256 for symbol in active_sorted})),
            membership_authority_hash=membership.authority_hash,
            source_freeze_content_hash=policy.source_freeze_content_hash,
            policy_version=policy.policy_version,
            algorithm_hash=policy.algorithm_hash,
        )
        events.append(event)
        for symbol in active_sorted:
            row = selected[symbol]
            masks.append(SlotMaskEntry(
                event_id,
                symbol,
                row.month,
                open_time_ms,
                "invalid_close_boundary" if symbol in invalid else "valid_minority",
                row.raw_line_sha256,
                row.archive_sha256,
            ))

    events.sort(key=lambda item: (item.open_time_ms, item.event_id))
    masks.sort(key=lambda item: (item.open_time_ms, item.symbol, item.event_id))
    blockers = sorted(set(blockers), key=lambda item: (item.open_time_ms or -1, item.reason, item.symbols))
    accounting = {
        "status": "blocked" if blockers else "accepted",
        "event_count": len(events),
        "invalid_rows_quarantined": sum(item.invalid_count for item in events),
        "valid_minority_rows_quarantined": sum(item.valid_minority_count for item in events),
        "total_rows_quarantined": len(masks),
        "full_slot_reconciliation": all(
            item.invalid_count + item.valid_minority_count == item.total_quarantined_count
            for item in events
        ),
        "raw_rows_rewritten": 0,
        "synthetic_fills": 0,
        "replacement_members": 0,
    }
    return PolicyEvaluation(tuple(events), tuple(masks), tuple(blockers), accounting)


def apply_invalid_interval_mask(
    rows: Iterable[VerifiedFiveMinuteRow],
    evaluation: PolicyEvaluation,
) -> tuple[VerifiedFiveMinuteRow, ...]:
    """Apply only the separately emitted full-slot mask; physical rows stay intact."""
    members = tuple(rows)
    by_key: dict[tuple[str, int], list[VerifiedFiveMinuteRow]] = {}
    for row in members:
        by_key.setdefault((row.symbol, row.open_time_ms), []).append(row)
    mask_by_key = {(item.symbol, item.open_time_ms): item for item in evaluation.masks}
    if len(mask_by_key) != len(evaluation.masks):
        raise PolicyHardBlock("duplicate mask entry")
    for key, mask in mask_by_key.items():
        physical = by_key.get(key, [])
        if len(physical) != 1 or physical[0].raw_line_sha256 != mask.raw_row_sha256:
            raise PolicyHardBlock("valid_minority_not_masked")
    for event in evaluation.events:
        masked = {item.symbol for item in evaluation.masks if item.event_id == event.event_id}
        if masked != set(event.active_members):
            raise PolicyHardBlock("valid_minority_not_masked")
    return tuple(row for row in members if (row.symbol, row.open_time_ms) not in mask_by_key)


def build_invalid_interval_manifests(
    policy: InvalidIntervalPolicy,
    membership: ActiveMembershipAuthority,
    evaluation: PolicyEvaluation,
    *,
    generated_utc: str | None = None,
) -> dict[str, dict[str, Any]]:
    contents: dict[str, Any] = {
        "invalid_interval_policy_manifest": {
            "policy_id": policy.document["policy_id"],
            "policy_version": policy.policy_version,
            "policy_canonical_hash": policy.canonical_hash,
            "algorithm_hash": policy.algorithm_hash,
            "authorizations": policy.document["authorizations"],
        },
        "invalid_interval_event_manifest": [asdict(item) for item in evaluation.events],
        "invalid_interval_slot_mask_manifest": [asdict(item) for item in evaluation.masks],
        "invalid_interval_accounting_manifest": {
            **evaluation.accounting,
            "blockers": [asdict(item) for item in evaluation.blockers],
            "evaluation_content_hash": evaluation.content_hash,
        },
    }
    output: dict[str, dict[str, Any]] = {}
    for manifest_type in ADR0015_MANIFEST_TYPES:
        identity = {
            "schema_version": 1,
            "manifest_type": manifest_type,
            "policy_canonical_hash": policy.canonical_hash,
            "source_freeze_content_hash": policy.source_freeze_content_hash,
            "membership_authority_hash": membership.authority_hash,
            "content": contents[manifest_type],
        }
        output[manifest_type] = {
            **identity,
            "content_hash": canonical_hash(identity),
            "generated_utc": generated_utc,
        }
    return output


def assert_order_content_identity(evaluations: Sequence[PolicyEvaluation]) -> str:
    hashes = {item.content_hash for item in evaluations}
    if len(evaluations) < 2 or len(hashes) != 1:
        raise PolicyHardBlock("order_content_hash_mismatch")
    return next(iter(hashes))
