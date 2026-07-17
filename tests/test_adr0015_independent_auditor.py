from __future__ import annotations

import random
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_adr0015 import (
    AuditFiveMinuteRow,
    IndependentMembershipAuthority,
    IndependentPolicyBlock,
    independent_hash,
    evaluate_candidate_slots,
    read_audit_five_minute_archive,
    wrap_policy_manifest,
)
from btc_eth_dual_quant.audit.liquid_universe_v4_adr0015_audit_run import (
    _accepted_close_precedes_blockers,
    _normalize_daily_source_periods,
    execute_adr0015_audit,
)


H = "a" * 64
A = "b" * 64
L = "c" * 64
ALG = "d" * 64
OPENED = 1_600_000_200_000


def row(symbol: str, *, invalid: bool = True, opened: int = OPENED) -> AuditFiveMinuteRow:
    closed = opened + (300_000 if invalid else 299_999)
    fields = (str(opened), "10", "12", "9", "11", "1", str(closed), "10", "1", "1", "10", "0")
    return AuditFiveMinuteRow.create(
        symbol=symbol, month="2020-09", fields=fields,
        raw_line=",".join(fields).encode(), line_number=1,
        archive_sha256=independent_hash(symbol), source_freeze_hash=H,
    )


def authority(count: int = 15, *, lifecycle=None) -> IndependentMembershipAuthority:
    members = [f"S{i:02d}" for i in range(count)]
    return IndependentMembershipAuthority.build(
        ({"month": "2020-09", "symbol": symbol} for symbol in members),
        lifecycle_end_exclusive_ms=lifecycle or {},
        membership_manifest_hash=A, lifecycle_registry_hash=L,
    )


class Adr0015IndependentAuditorTests(unittest.TestCase):
    def evaluate(self, rows, auth=None):
        return evaluate_candidate_slots(
            rows, authority=auth or authority(), source_freeze_hash=H,
            policy_version="ADR-0015-V1", algorithm_hash=ALG,
        )

    def test_accepts_15_of_15_and_12_of_15(self):
        all_invalid = self.evaluate([row(f"S{i:02d}") for i in range(15)])
        threshold = self.evaluate([row(f"S{i:02d}", invalid=i < 12) for i in range(15)])
        self.assertEqual(all_invalid["accounting"]["invalid_rows_quarantined"], 15)
        self.assertEqual(threshold["accounting"]["valid_minority_rows_quarantined"], 3)
        self.assertEqual(len(threshold["slot_mask"]), 15)

    def test_valid_minority_is_masked_at_14_of_15(self):
        result = self.evaluate([row(f"S{i:02d}", invalid=i < 14) for i in range(15)])
        self.assertEqual(result["events"][0]["valid_minority_members"], ["S14"])
        self.assertEqual(result["slot_mask"][-1]["classification"], "valid_minority")

    def test_lifecycle_end_exclusive_reduces_denominator(self):
        auth = authority(lifecycle={"S14": OPENED})
        result = self.evaluate([row(f"S{i:02d}") for i in range(14)], auth)
        self.assertEqual(result["events"][0]["total_quarantined_count"], 14)

    def test_input_order_has_identical_output(self):
        rows = [row(f"S{i:02d}", invalid=i < 14) for i in range(15)]
        expected = self.evaluate(rows)
        reversed_result = self.evaluate(reversed(rows))
        shuffled = list(rows)
        random.Random(15001).shuffle(shuffled)
        self.assertEqual(expected, reversed_result)
        self.assertEqual(expected, self.evaluate(shuffled))

    def test_fail_closed_faults(self):
        base = [row(f"S{i:02d}") for i in range(15)]
        faults = [
            base[:-1],
            base + [base[0]],
            [*base[:-1], row("OUTSIDE")],
            [row(f"S{i:02d}", invalid=i < 11) for i in range(15)],
        ]
        for values in faults:
            with self.subTest(size=len(values)), self.assertRaises(IndependentPolicyBlock):
                self.evaluate(values)

    def test_rejects_raw_row_timestamp_and_ohlcv_tampering(self):
        good = row("S00")
        cases = [
            {"raw_line": good.raw_line + b"x", "fields": good.fields},
            {"raw_line": b"bad", "fields": good.fields},
            {"raw_line": b"1600000200001,10,12,9,11,1,1600000500001,10,1,1,10,0",
             "fields": ("1600000200001", "10", "12", "9", "11", "1", "1600000500001", "10", "1", "1", "10", "0")},
            {"raw_line": b"1600000200000,10,8,9,11,1,1600000500000,10,1,1,10,0",
             "fields": ("1600000200000", "10", "8", "9", "11", "1", "1600000500000", "10", "1", "1", "10", "0")},
        ]
        for case in cases:
            with self.subTest(case=case["raw_line"]), self.assertRaises(IndependentPolicyBlock):
                AuditFiveMinuteRow.create(
                    symbol="S00", month="2020-09", line_number=1,
                    archive_sha256=A, source_freeze_hash=H, **case,
                )

    def test_event_identity_binds_all_authorities(self):
        result = self.evaluate([row(f"S{i:02d}") for i in range(15)])
        event_id = result["events"][0]["event_id"]
        for changed in ("e" * 64, "f" * 64):
            actual = evaluate_candidate_slots(
                [row(f"S{i:02d}") for i in range(15)], authority=authority(),
                source_freeze_hash=H, policy_version="ADR-0015-V1", algorithm_hash=changed,
            )
            self.assertNotEqual(event_id, actual["events"][0]["event_id"])

    def test_exact_zip_member_and_archive_revision_are_verified(self):
        fields = (str(OPENED), "10", "12", "9", "11", "1", str(OPENED + 299_999), "10", "1", "1", "10", "0")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "S00-5m-2020-09.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("S00-5m-2020-09.csv", ",".join(fields))
            payload = path.read_bytes()
            frozen = {
                "canonical_key": "data/spot/monthly/klines/S00/5m/S00-5m-2020-09.zip",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_size": len(payload),
            }
            rows = read_audit_five_minute_archive(
                path, frozen=frozen, symbol="S00", month="2020-09", source_freeze_hash=H,
            )
            self.assertEqual(len(rows), 1)
            frozen["byte_size"] += 1
            with self.assertRaises(IndependentPolicyBlock):
                read_audit_five_minute_archive(
                    path, frozen=frozen, symbol="S00", month="2020-09", source_freeze_hash=H,
                )

    def test_generated_time_is_not_part_of_policy_manifest_identity(self):
        manifest = wrap_policy_manifest(
            "invalid_interval_event_manifest", [], authority_hash=A,
            policy_hash=L, source_freeze_hash=H,
        )
        changed = dict(manifest, generated_utc="2099-01-01T00:00:00Z")
        self.assertEqual(manifest["content_hash"], changed["content_hash"])

    def test_native_microsecond_close_boundary_normalizes_without_repair(self):
        open_ms = 1_893_456_000_000
        fields = (
            str(open_ms * 1_000), "10", "12", "9", "11", "1",
            str(open_ms * 1_000 + 299_999_999), "10", "1", "1", "10", "0",
        )
        row = AuditFiveMinuteRow.create(
            symbol="S00", month="2030-01", fields=fields,
            raw_line=(",".join(fields)).encode(), line_number=1,
            archive_sha256=H, source_freeze_hash=L,
        )
        self.assertEqual(row.open_time_ms, open_ms)
        self.assertEqual(row.close_time_ms, open_ms + 299_999)
        self.assertFalse(row.has_close_boundary_defect)

    def test_daily_source_period_keeps_full_authority_date(self):
        rows = [{
            "canonical_key": "data/spot/daily/klines/AXSUSDT/1d/AXSUSDT-1d-2026-02-10.zip",
            "archive_month": "2026-02",
        }]
        _normalize_daily_source_periods(rows)
        self.assertEqual(rows[0]["archive_month"], "2026-02-10")

    def test_only_accepted_event_members_clear_close_precedes_blocker(self):
        evaluation = {"events": [{
            "open_time_ms": 1_609_459_000_000,
            "invalid_members": ["ADAUSDT", "BTCUSDT"],
        }]}
        self.assertEqual(
            _accepted_close_precedes_blockers(evaluation),
            {"ADAUSDT:2020-12:close precedes open", "BTCUSDT:2020-12:close precedes open"},
        )

    def test_real_run_requires_separate_exact_head_review_authorization(self):
        protocol = {"audit_scope": {"traversal_orders": []}}
        with self.assertRaises(ValueError):
            execute_adr0015_audit(
                repository=Path("."), raw_root=Path("."), protocol=protocol,
                review={"verdict": "approve", "remaining_critical_findings": 0,
                        "remaining_high_findings": 0, "full_independent_audit_run_authorized": False},
            )

    def test_real_run_rejects_unbound_approval(self):
        protocol = {"audit_scope": {"traversal_orders": []}}
        with self.assertRaisesRegex(ValueError, "binding changed"):
            execute_adr0015_audit(
                repository=Path("."), raw_root=Path("."), protocol=protocol,
                review={"verdict": "approve", "remaining_critical_findings": 0,
                        "remaining_high_findings": 0, "full_independent_audit_run_authorized": True},
            )


if __name__ == "__main__":
    unittest.main()
