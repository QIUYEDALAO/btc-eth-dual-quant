"""Independent ADR-0015 event, slot-mask, and accounting recomputation.

This audit-sidecar code intentionally does not import the production invalid-
interval implementation.  It preserves physical-row identity and fails closed
when a candidate slot cannot be reconciled with point-in-time membership.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence
import zipfile


FIVE_MINUTE_MS = 300_000
NORMAL_CLOSE_DELTA_MS = 299_999


class IndependentPolicyBlock(ValueError):
    """An evidence or policy condition prevents an audit conclusion."""


def independent_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise IndependentPolicyBlock(f"malformed {label}")
    return value


def _uint(value: str, label: str) -> int:
    if not value or not value.isascii() or not value.isdigit():
        raise IndependentPolicyBlock(f"malformed {label}")
    result = int(value)
    if result >= 10**14:
        if result % 1_000:
            raise IndependentPolicyBlock(f"unaligned microsecond {label}")
        result //= 1_000
    if result < 10**11 or result >= 10**14:
        raise IndependentPolicyBlock(f"unsupported {label} unit")
    return result


def _number(value: str, label: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise IndependentPolicyBlock(f"malformed {label}") from exc
    if not result.is_finite():
        raise IndependentPolicyBlock(f"non-finite {label}")
    return result


@dataclass(frozen=True)
class AuditFiveMinuteRow:
    symbol: str
    month: str
    fields: tuple[str, ...]
    raw_line: bytes
    line_number: int
    archive_sha256: str
    source_freeze_hash: str

    @classmethod
    def create(
        cls,
        *,
        symbol: str,
        month: str,
        fields: Sequence[str],
        raw_line: bytes,
        line_number: int,
        archive_sha256: str,
        source_freeze_hash: str,
    ) -> "AuditFiveMinuteRow":
        row = cls(
            symbol=symbol,
            month=month,
            fields=tuple(fields),
            raw_line=bytes(raw_line),
            line_number=line_number,
            archive_sha256=_sha(archive_sha256, "archive hash"),
            source_freeze_hash=_sha(source_freeze_hash, "source-freeze hash"),
        )
        row.verify()
        return row

    @property
    def raw_row_sha256(self) -> str:
        return _sha256_bytes(self.raw_line)

    @property
    def open_time_ms(self) -> int:
        return _uint(self.fields[0], "open time")

    @property
    def close_time_ms(self) -> int:
        return _uint(self.fields[6], "close time")

    @property
    def has_close_boundary_defect(self) -> bool:
        return self.close_time_ms != self.open_time_ms + NORMAL_CLOSE_DELTA_MS

    def verify(self) -> None:
        if len(self.fields) != 12:
            raise IndependentPolicyBlock("non-12-field kline")
        decoded = self.raw_line.decode("utf-8-sig" if self.line_number == 1 else "utf-8")
        parsed = tuple(item.strip() for item in next(csv.reader(io.StringIO(decoded))))
        if parsed != self.fields:
            raise IndependentPolicyBlock("raw-row identity mismatch")
        if self.line_number < 1 or not self.symbol or len(self.month) != 7:
            raise IndependentPolicyBlock("row authority is malformed")
        opened = self.open_time_ms
        _ = self.close_time_ms
        if opened % FIVE_MINUTE_MS:
            raise IndependentPolicyBlock("off-grid open time")
        open_, high, low, close = (_number(self.fields[i], "price") for i in (1, 2, 3, 4))
        quantities = tuple(_number(self.fields[i], "quantity") for i in (5, 7, 9, 10))
        if low > min(open_, close) or high < max(open_, close) or low > high:
            raise IndependentPolicyBlock("OHLC legality failure")
        if any(item < 0 for item in quantities):
            raise IndependentPolicyBlock("negative volume")
        if not self.fields[8].isdigit():
            raise IndependentPolicyBlock("malformed trade count")


def read_audit_five_minute_archive(
    path: Path,
    *,
    frozen: Mapping[str, Any],
    symbol: str,
    month: str,
    source_freeze_hash: str,
) -> tuple[AuditFiveMinuteRow, ...]:
    """Read one exact frozen ZIP without using the production archive reader."""
    payload = path.read_bytes()
    archive_hash = _sha256_bytes(payload)
    if archive_hash != frozen.get("sha256") or len(payload) != frozen.get("byte_size"):
        raise IndependentPolicyBlock("source archive revision")
    key = str(frozen.get("canonical_key", ""))
    if not key.endswith(f"/{symbol}/5m/{symbol}-5m-{month}.zip"):
        raise IndependentPolicyBlock("archive key identity mismatch")
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if archive.testzip() is not None:
                raise IndependentPolicyBlock("archive CRC failure")
            members = [item for item in archive.infolist() if not item.is_dir()]
            if len(members) != 1:
                raise IndependentPolicyBlock("archive member count mismatch")
            member = members[0]
            if PurePosixPath(member.filename).name != f"{symbol}-5m-{month}.csv":
                raise IndependentPolicyBlock("archive member identity mismatch")
            raw_lines = archive.read(member).splitlines()
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise IndependentPolicyBlock("invalid frozen ZIP") from exc
    output: list[AuditFiveMinuteRow] = []
    for line_number, raw_line in enumerate(raw_lines, start=1):
        try:
            text = raw_line.decode("utf-8-sig" if line_number == 1 else "utf-8")
        except UnicodeDecodeError as exc:
            raise IndependentPolicyBlock("invalid CSV encoding") from exc
        records = list(csv.reader(io.StringIO(text)))
        if len(records) != 1:
            raise IndependentPolicyBlock("ambiguous physical CSV row")
        fields = tuple(item.strip() for item in records[0])
        if line_number == 1 and fields and not fields[0].isdigit():
            continue
        output.append(AuditFiveMinuteRow.create(
            symbol=symbol,
            month=month,
            fields=fields,
            raw_line=raw_line,
            line_number=line_number,
            archive_sha256=archive_hash,
            source_freeze_hash=source_freeze_hash,
        ))
    return tuple(output)


@dataclass(frozen=True)
class IndependentMembershipAuthority:
    members_by_month: Mapping[str, tuple[str, ...]]
    lifecycle_end_exclusive_ms: Mapping[str, int]
    membership_manifest_hash: str
    lifecycle_registry_hash: str
    authority_hash: str

    @classmethod
    def build(
        cls,
        membership_rows: Iterable[Mapping[str, Any]],
        *,
        lifecycle_end_exclusive_ms: Mapping[str, int],
        membership_manifest_hash: str,
        lifecycle_registry_hash: str,
    ) -> "IndependentMembershipAuthority":
        months: dict[str, list[str]] = {}
        for row in membership_rows:
            month = row.get("month", str(row.get("effective_month", ""))[:7])
            symbol = row.get("symbol")
            if not isinstance(month, str) or not isinstance(symbol, str):
                raise IndependentPolicyBlock("malformed membership row")
            months.setdefault(month, []).append(symbol)
        normalized: dict[str, tuple[str, ...]] = {}
        for month, symbols in months.items():
            if len(symbols) != len(set(symbols)):
                raise IndependentPolicyBlock("duplicate membership row")
            normalized[month] = tuple(sorted(symbols))
        mh = _sha(membership_manifest_hash, "membership manifest hash")
        lh = _sha(lifecycle_registry_hash, "lifecycle registry hash")
        identity = {
            "membership_manifest_content_hash": mh,
            "lifecycle_registry_hash": lh,
            "active_member_rule": "month_start_membership_minus_end_exclusive_lifecycle_termination",
        }
        return cls(normalized, dict(lifecycle_end_exclusive_ms), mh, lh, independent_hash(identity))

    def active_members(self, month: str, open_time_ms: int) -> tuple[str, ...]:
        if month not in self.members_by_month:
            raise IndependentPolicyBlock("membership month missing")
        return tuple(
            symbol for symbol in self.members_by_month[month]
            if self.lifecycle_end_exclusive_ms.get(symbol, open_time_ms + 1) > open_time_ms
        )


def _event_id(
    source_freeze_hash: str,
    authority_hash: str,
    policy_version: str,
    algorithm_hash: str,
    open_time_ms: int,
) -> str:
    return independent_hash({
        "source_freeze_content_hash": source_freeze_hash,
        "membership_authority_hash": authority_hash,
        "policy_version": policy_version,
        "algorithm_hash": algorithm_hash,
        "open_time_ms": open_time_ms,
    })


def evaluate_candidate_slots(
    rows: Iterable[AuditFiveMinuteRow],
    *,
    authority: IndependentMembershipAuthority,
    source_freeze_hash: str,
    policy_version: str,
    algorithm_hash: str,
) -> dict[str, Any]:
    source_hash = _sha(source_freeze_hash, "source-freeze hash")
    algorithm = _sha(algorithm_hash, "algorithm hash")
    grouped: dict[int, list[AuditFiveMinuteRow]] = {}
    for row in rows:
        row.verify()
        if row.source_freeze_hash != source_hash:
            raise IndependentPolicyBlock("row source-freeze hash drift")
        grouped.setdefault(row.open_time_ms, []).append(row)
    events: list[dict[str, Any]] = []
    mask: list[dict[str, Any]] = []
    for opened, slot_rows in sorted(grouped.items()):
        months = {row.month for row in slot_rows}
        if len(months) != 1:
            raise IndependentPolicyBlock("candidate slot month conflict")
        month = next(iter(months))
        active = authority.active_members(month, opened)
        by_symbol: dict[str, AuditFiveMinuteRow] = {}
        for row in slot_rows:
            if row.symbol not in active:
                raise IndependentPolicyBlock("non-member row")
            if row.symbol in by_symbol:
                raise IndependentPolicyBlock("duplicate active-member row")
            by_symbol[row.symbol] = row
        if set(by_symbol) != set(active):
            raise IndependentPolicyBlock("missing active-member row")
        invalid = tuple(symbol for symbol in active if by_symbol[symbol].has_close_boundary_defect)
        if len(invalid) < 2 or len(invalid) * 5 < len(active) * 4:
            raise IndependentPolicyBlock("candidate threshold not met")
        event_id = _event_id(source_hash, authority.authority_hash, policy_version, algorithm, opened)
        invalid_set = set(invalid)
        valid_minority = tuple(symbol for symbol in active if symbol not in invalid_set)
        events.append({
            "active_members": list(active),
            "algorithm_hash": algorithm,
            "event_id": event_id,
            "invalid_count": len(invalid),
            "invalid_members": list(invalid),
            "membership_authority_hash": authority.authority_hash,
            "open_time_ms": opened,
            "policy_version": policy_version,
            "raw_row_hashes": [by_symbol[symbol].raw_row_sha256 for symbol in active],
            "source_archive_hashes": sorted({by_symbol[symbol].archive_sha256 for symbol in active}),
            "source_freeze_content_hash": source_hash,
            "total_quarantined_count": len(active),
            "valid_minority_count": len(valid_minority),
            "valid_minority_members": list(valid_minority),
        })
        for symbol in active:
            row = by_symbol[symbol]
            mask.append({
                "archive_sha256": row.archive_sha256,
                "classification": "invalid_close_boundary" if symbol in invalid_set else "valid_minority",
                "event_id": event_id,
                "month": month,
                "open_time_ms": opened,
                "raw_row_sha256": row.raw_row_sha256,
                "symbol": symbol,
            })
    invalid_count = sum(event["invalid_count"] for event in events)
    total_count = sum(event["total_quarantined_count"] for event in events)
    accounting = {
        "event_count": len(events),
        "full_slot_reconciliation": total_count == len(mask),
        "invalid_rows_quarantined": invalid_count,
        "raw_rows_rewritten": 0,
        "replacement_members": 0,
        "status": "accepted",
        "synthetic_fills": 0,
        "total_rows_quarantined": total_count,
        "valid_minority_rows_quarantined": total_count - invalid_count,
    }
    evaluation_hash = independent_hash({
        "events": events,
        "masks": mask,
        "blockers": [],
        "accounting": accounting,
    })
    manifest_accounting = {
        **accounting,
        "blockers": [],
        "evaluation_content_hash": evaluation_hash,
    }
    return {"events": events, "slot_mask": mask, "accounting": manifest_accounting}


def wrap_policy_manifest(
    manifest_type: str,
    content: Any,
    *,
    authority_hash: str,
    policy_hash: str,
    source_freeze_hash: str,
) -> dict[str, Any]:
    document = {
        "schema_version": 1,
        "manifest_type": manifest_type,
        "content": content,
        "membership_authority_hash": _sha(authority_hash, "membership authority hash"),
        "policy_canonical_hash": _sha(policy_hash, "policy hash"),
        "source_freeze_content_hash": _sha(source_freeze_hash, "source-freeze hash"),
    }
    document["content_hash"] = independent_hash(document)
    document["generated_utc"] = None
    return document
