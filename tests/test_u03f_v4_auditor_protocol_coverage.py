import io
import json
import tempfile
import unittest
import zipfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import (
    REQUIRED_AUDIT_ARTIFACTS,
    audit_artifact_set_hash,
    build_audit_artifacts,
    compare_artifact_suite,
    make_manifest,
    scan_copied_production_functions,
    verify_file_hash,
    verify_manifest_wrapper,
)
from btc_eth_dual_quant.audit.liquid_universe_v4_independent import (
    FiveMinuteBar,
    active_universe_at,
    apply_resolution_registry,
    audit_canonical_json,
    audit_five_minute_grid,
    classify_lifecycle_rows,
    classify_member_gaps,
    complete_day_mask,
    eligibility_and_membership,
    milliseconds_from_utc,
    parse_official_kline_zip,
    raw_row_hash,
    strict_json_loads,
    validate_lifecycle_registry,
    verify_source_freeze,
)


def raw_row(timestamp: int = 1_577_836_800_000, volume: str = "1") -> list[str]:
    return [
        str(timestamp), "1", "2", "0.5", "1.5", volume,
        str(timestamp + 86_399_999), "2", "3", "0.4", "0.8", "0",
    ]


def zip_payload(symbol: str, interval: str, period: str, rows: list[list[str]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{symbol}-{interval}-{period}.csv", "\n".join(",".join(row) for row in rows) + "\n")
    return buffer.getvalue()


def lifecycle_fixture(row_hashes: list[tuple[int, str]] | None = None):
    event = {
        "event_id": "ASSET-SPOT-2024-01-02-STOP",
        "symbol": "ASSETUSDT",
        "known_at": "2024-01-01T00:00:00Z",
        "effective_at": "2024-01-02T03:00:00Z",
        "availability_end_exclusive": "2024-01-02T03:00:00Z",
        "last_valid_market_time": "2024-01-02T02:59:59.999Z",
        "successor_authority": "provenance_only",
        "policy_version": "ADR-X",
        "official_evidence_hashes": ["1" * 64],
        "archive_hashes": ["2" * 64],
        "intraday_evidence_hashes": ["3" * 64],
        "similar_scope_scan_hash": "4" * 64,
        "adjudication_hash": "5" * 64,
        "affected_raw_rows": [
            {
                "interval": "1d",
                "open_time_ms": timestamp,
                "raw_row_sha256": digest,
                "classification": "registered_lifecycle_affected_row",
                "source_archive_hashes": ["2" * 64],
            }
            for timestamp, digest in (row_hashes or [])
        ],
    }
    policy = {
        "schema_version": 1,
        "policy_id": "POLICY",
        "policy_version": "ADR-X",
        "semantics": {
            "availability_bounds": "start_inclusive_end_exclusive",
            "integer_epoch_only": True,
            "availability_mask_before_expected_grid": True,
            "post_boundary_absence_is_gap": False,
            "partial_days_enter_ranking_or_history": False,
            "month_start_membership_rewritten_mid_month": False,
            "successor_inherits_history_or_rank": False,
        },
    }
    registry = {"schema_version": 1, "policy_id": "POLICY", "policy_version": "ADR-X", "entries": [event]}
    return policy, registry


class CanonicalAndArchiveCoverageTests(unittest.TestCase):
    def test_strict_json_and_canonical_metadata_rules(self):
        self.assertEqual(strict_json_loads('{"a":1}'), {"a": 1})
        with self.assertRaises(ValueError):
            strict_json_loads('{"a":1,"a":2}')
        with self.assertRaises(ValueError):
            strict_json_loads('{"a":NaN}')
        self.assertEqual(
            audit_canonical_json({"b": Decimal("1.00"), "generated_utc": "later", "a": 2}),
            '{"a":2,"b":"1.00"}',
        )

    def test_official_zip_crc_schema_identity_and_freeze(self):
        payload = zip_payload("BTCUSDT", "1d", "2020-01", [raw_row()])
        parsed = parse_official_kline_zip(payload, symbol="BTCUSDT", interval="1d", archive_period="2020-01")
        self.assertEqual(len(parsed.rows), 1)
        key = "data/spot/monthly/BTCUSDT.zip"
        freeze = [{"canonical_key": key, "sha256": parsed.sha256, "byte_size": len(payload)}]
        self.assertEqual(verify_source_freeze(freeze, {key: payload})[0]["sha256"], parsed.sha256)
        with self.assertRaises(ValueError):
            verify_source_freeze(freeze, {key: payload + b"tamper"})
        with self.assertRaises(ValueError):
            parse_official_kline_zip(payload, symbol="ETHUSDT", interval="1d", archive_period="2020-01")

    def test_archive_duplicate_or_out_of_period_row_fails(self):
        duplicate = zip_payload("BTCUSDT", "1d", "2020-01", [raw_row(), raw_row()])
        with self.assertRaises(ValueError):
            parse_official_kline_zip(duplicate, symbol="BTCUSDT", interval="1d", archive_period="2020-01")
        outside = zip_payload("BTCUSDT", "1d", "2020-01", [raw_row(1_580_515_200_000)])
        with self.assertRaises(ValueError):
            parse_official_kline_zip(outside, symbol="BTCUSDT", interval="1d", archive_period="2020-01")
        corrupted = bytearray(zip_payload("BTCUSDT", "1d", "2020-01", [raw_row()]))
        corrupted[len(corrupted) // 2] ^= 0xFF
        with self.assertRaises(ValueError):
            parse_official_kline_zip(bytes(corrupted), symbol="BTCUSDT", interval="1d", archive_period="2020-01")


class RegistryAndLifecycleCoverageTests(unittest.TestCase):
    def test_registry_driven_daily_correction_and_source_tamper(self):
        invalid = raw_row(volume="-1")
        corrected = raw_row(volume="1")
        monthly_key, daily_key = "monthly.zip", "daily.zip"
        rule = {
            "symbol": "BTTUSDT",
            "open_time_utc": "2020-01-01T00:00:00Z",
            "resolution_id": "R1",
            "approved_action": "replace_invalid_monthly_with_daily",
            "monthly_archive": {
                "canonical_key": monthly_key,
                "sha256": "a" * 64,
                "raw_row_hashes": [raw_row_hash(invalid)],
            },
            "daily_archive": {
                "canonical_key": daily_key,
                "sha256": "b" * 64,
                "raw_row_hashes": [raw_row_hash(corrected)],
                "raw_rows": [corrected],
            },
        }
        rows, quarantine, resolutions = apply_resolution_registry(
            symbol="BTTUSDT",
            monthly_rows=[invalid],
            daily_rows=[corrected],
            registry_entries=[rule],
            archive_hashes={monthly_key: "a" * 64, daily_key: "b" * 64},
        )
        self.assertEqual(rows[0].base_volume, Decimal("1"))
        self.assertEqual(len(quarantine), 1)
        self.assertEqual(resolutions[0]["action"], "replace_invalid_monthly_with_daily")
        with self.assertRaises(ValueError):
            apply_resolution_registry(
                symbol="BTTUSDT", monthly_rows=[invalid], daily_rows=[corrected], registry_entries=[rule],
                archive_hashes={monthly_key: "0" * 64, daily_key: "b" * 64},
            )

    def test_registry_driven_duplicate_and_unknown_duplicate(self):
        row = raw_row(1_770_681_600_000)
        rule = {
            "symbol": "AXSUSDT",
            "open_time_utc": "2026-02-10T00:00:00Z",
            "resolution_id": "R2",
            "approved_action": "collapse_byte_identical_duplicate",
            "monthly_archive": {"canonical_key": "m", "sha256": "a" * 64, "raw_row_hashes": [raw_row_hash(row)] * 2},
            "daily_archive": {},
        }
        rows, quarantine, _ = apply_resolution_registry(
            symbol="AXSUSDT", monthly_rows=[row, row], daily_rows=[], registry_entries=[rule], archive_hashes={"m": "a" * 64}
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(quarantine), 1)
        with self.assertRaises(ValueError):
            apply_resolution_registry(
                symbol="AXSUSDT", monthly_rows=[row, row], daily_rows=[], registry_entries=[], archive_hashes={}
            )
        with self.assertRaises(ValueError):
            apply_resolution_registry(
                symbol="AXSUSDT", monthly_rows=[row, row, row], daily_rows=[], registry_entries=[rule], archive_hashes={"m": "a" * 64}
            )

    def test_lifecycle_registry_affected_rows_and_new_post_event_row(self):
        rows = [raw_row(1_704_153_600_000), raw_row(1_704_240_000_000)]
        bindings = [(int(row[0]), raw_row_hash(row)) for row in rows]
        policy, registry = lifecycle_fixture(bindings)
        event = validate_lifecycle_registry(policy, registry, research_start="2020-01-01T00:00:00Z")[0]
        quarantine, blocked = classify_lifecycle_rows(event, rows)
        self.assertEqual(len(quarantine), 2)
        self.assertEqual(blocked, [])
        extra = raw_row(1_704_326_400_000)
        quarantine, blocked = classify_lifecycle_rows(event, rows + [extra])
        self.assertEqual(len(blocked), 1)
        changed = json.loads(json.dumps(registry))
        changed["entries"][0]["affected_raw_rows"][0]["raw_row_sha256"] = "0" * 64
        changed_event = validate_lifecycle_registry(policy, changed, research_start="2020-01-01T00:00:00Z")[0]
        with self.assertRaises(ValueError):
            classify_lifecycle_rows(changed_event, rows)

    def test_lifecycle_overlap_or_successor_inheritance_fails(self):
        policy, registry = lifecycle_fixture()
        inherited = json.loads(json.dumps(registry))
        inherited["entries"][0]["successor_authority"] = "inherits_history"
        with self.assertRaises(ValueError):
            validate_lifecycle_registry(policy, inherited, research_start="2020-01-01T00:00:00Z")
        overlap = json.loads(json.dumps(registry))
        second = json.loads(json.dumps(overlap["entries"][0]))
        second["event_id"] = "SECOND"
        second["known_at"] = "2024-01-01T01:00:00Z"
        overlap["entries"].append(second)
        with self.assertRaises(ValueError):
            validate_lifecycle_registry(policy, overlap, research_start="2020-01-01T00:00:00Z")
        changed_boundary = json.loads(json.dumps(registry))
        changed_boundary["entries"][0]["effective_at"] = "2024-01-02T04:00:00Z"
        with self.assertRaises(ValueError):
            validate_lifecycle_registry(policy, changed_boundary, research_start="2020-01-01T00:00:00Z")

    def test_lifecycle_frozen_hash_bindings_fail_closed(self):
        policy, registry = lifecycle_fixture()
        policy["canonical_hash"] = "a" * 64
        registry["canonical_hash"] = "b" * 64
        registry["reviewed_event_set_hash"] = "c" * 64
        validate_lifecycle_registry(
            policy,
            registry,
            research_start="2020-01-01T00:00:00Z",
            expected_policy_hash="a" * 64,
            expected_registry_hash="b" * 64,
            expected_reviewed_event_set_hash="c" * 64,
        )
        with self.assertRaises(ValueError):
            validate_lifecycle_registry(
                policy,
                registry,
                research_start="2020-01-01T00:00:00Z",
                expected_policy_hash="a" * 64,
                expected_registry_hash="0" * 64,
                expected_reviewed_event_set_hash="c" * 64,
            )


class MembershipGridAndAvailabilityCoverageTests(unittest.TestCase):
    def test_exact_365_90_windows_tie_break_exclusion_and_future_exclusion(self):
        effective = date(2024, 1, 1)
        history = {effective - timedelta(days=offset): Decimal("10") for offset in range(1, 366)}
        data = {"AAAUSDT": dict(history), "BBBUSDT": dict(history), "STABLEUSDT": dict(history)}
        data["AAAUSDT"][effective] = Decimal("999999")
        candidates, membership = eligibility_and_membership(
            effective_month="2024-01", daily_quote_volumes=data, excluded_symbols={"STABLEUSDT"}, target_size=2
        )
        self.assertEqual([item["symbol"] for item in membership], ["AAAUSDT", "BBBUSDT"])
        self.assertEqual(membership[0]["median_daily_quote_volume_90d"], "10")
        self.assertEqual(next(item for item in candidates if item["symbol"] == "STABLEUSDT")["reason"], "excluded_by_contract")
        del data["BBBUSDT"][effective - timedelta(days=365)]
        _, membership = eligibility_and_membership(effective_month="2024-01", daily_quote_volumes=data, target_size=3)
        self.assertNotIn("BBBUSDT", [item["symbol"] for item in membership])

    def test_availability_mask_precedes_grid_and_missing_hour_is_visible(self):
        start = milliseconds_from_utc("2024-01-01T00:00:00Z")
        boundary = milliseconds_from_utc("2024-01-01T01:00:00Z")
        bars = [FiveMinuteBar(start + index * 300_000, Decimal("1"), Decimal("2"), Decimal("0.5"), Decimal("1.5"), Decimal("1")) for index in range(12)]
        audit = audit_five_minute_grid(symbol="ASSETUSDT", month="2024-01", bars=bars, availability_end_exclusive_ms=boundary)
        self.assertEqual(len(audit.expected_slots), 12)
        self.assertEqual(audit.missing_slots, ())
        missing = audit_five_minute_grid(symbol="ASSETUSDT", month="2024-01", bars=bars[:-1], availability_end_exclusive_ms=boundary)
        self.assertEqual(len(missing.missing_slots), 1)
        post_boundary_absence = audit_five_minute_grid(
            symbol="ASSETUSDT", month="2024-01", bars=bars, availability_end_exclusive_ms=boundary
        )
        self.assertNotIn(boundary, post_boundary_absence.missing_slots)

    def test_gap_attribution_and_no_manual_replacement(self):
        self.assertEqual(
            classify_member_gaps(member_missing_slots={"A": {1}, "B": {1}}),
            {"A": "global_outage", "B": "global_outage"},
        )
        self.assertEqual(
            classify_member_gaps(member_missing_slots={"A": {1, 2}, "B": {1}})["A"],
            "unresolved_blocked",
        )
        self.assertEqual(
            classify_member_gaps(member_missing_slots={"A": {1, 2}, "B": {1}}, confirmed_symbol_months={"A"})["A"],
            "symbol_month_quarantine",
        )

    def test_partial_day_and_active_universe_keep_membership(self):
        policy, registry = lifecycle_fixture()
        event = validate_lifecycle_registry(policy, registry, research_start="2020-01-01T00:00:00Z")[0]
        day = date(2024, 1, 2)
        start = milliseconds_from_utc("2024-01-02T00:00:00Z")
        observed = {start + index * 300_000 for index in range(36)}
        mask = complete_day_mask(day=day, observed_slots=observed, availability_end_exclusive_ms=event.availability_end_exclusive_ms)
        self.assertTrue(mask["partial_lifecycle_day"])
        self.assertFalse(mask["complete"])
        before = active_universe_at(membership=["ASSETUSDT", "OTHERUSDT"], timestamp_ms=start, lifecycle_events=[event])
        after = active_universe_at(membership=["ASSETUSDT", "OTHERUSDT"], timestamp_ms=event.availability_end_exclusive_ms, lifecycle_events=[event])
        self.assertEqual(len(before), len(after))
        self.assertEqual(after[0]["state"], "lifecycle_terminated")


class ArtifactAndFaultCoverageTests(unittest.TestCase):
    def test_all_required_artifacts_and_exact_suite_comparison(self):
        contents = {name: [] if name.endswith("manifest") else {} for name in REQUIRED_AUDIT_ARTIFACTS}
        one = build_audit_artifacts(contents, contract_hash="c" * 64, lifecycle_registry_hash="r" * 64)
        two = build_audit_artifacts(dict(reversed(list(contents.items()))), contract_hash="c" * 64, lifecycle_registry_hash="r" * 64)
        self.assertEqual(audit_artifact_set_hash(one), audit_artifact_set_hash(two))
        self.assertTrue(compare_artifact_suite(one, two)["exact"])
        changed = json.loads(json.dumps(two))
        changed["membership_manifest"]["content"] = [{"symbol": "tampered"}]
        self.assertFalse(compare_artifact_suite(one, changed)["exact"])

    def test_manifest_and_report_tamper_are_rejected(self):
        manifest = make_manifest("fixture", [{"a": 1}])
        self.assertTrue(verify_manifest_wrapper(manifest))
        changed = json.loads(json.dumps(manifest))
        changed["content"][0]["a"] = 2
        with self.assertRaises(ValueError):
            verify_manifest_wrapper(changed)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            path.write_text("frozen", encoding="utf-8")
            digest = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
            self.assertEqual(verify_file_hash(path, digest), digest)
            path.write_text("changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_file_hash(path, digest)

    def test_copied_function_body_is_detected(self):
        production = "def prod(x):\n    y = x + 1\n    return y * 2\n"
        copied = "def renamed(x):\n    y = x + 1\n    return y * 2\n"
        self.assertTrue(scan_copied_production_functions(copied, [production]))
        self.assertEqual(scan_copied_production_functions("def own(x):\n    return x\n", [production]), [])
