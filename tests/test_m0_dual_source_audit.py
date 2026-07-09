from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import m0_dual_source_audit

from btc_eth_dual_quant.data.dual_source_audit import (
    AuditRunEvidence,
    ScopePlan,
    compare_scope,
    evaluate_gate,
    render_diagnostics_report,
    render_revalidation_report,
    source_failure,
)


def row(
    open_time: int = 0,
    *,
    open_price: str = "100",
    high: str = "110",
    low: str = "90",
    close: str = "105",
    volume: str = "10",
    quote_volume: str = "1000",
) -> dict[str, object]:
    return {
        "open_time": open_time,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "close_time": open_time + 3_599_999,
        "quote_volume": quote_volume,
        "trade_count": 5,
        "taker_buy_base_volume": "4",
        "taker_buy_quote_volume": "400",
    }


class DualSourceComparisonTests(unittest.TestCase):
    def test_decimal_equivalent_raw_values_are_format_only(self) -> None:
        zip_row = row(open_price="100.00000000")
        rest_row = row(open_price="100")
        evidence = compare_scope(
            plan=ScopePlan("spot_klines", "BTCUSDT", "1h", "2020-01", ("first",)),
            zip_rows=[zip_row],
            rest_rows=[rest_row],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        self.assertEqual(evidence.classification_counts["format_only"], 1)
        self.assertEqual(evidence.classification_counts["source_revision"], 0)
        self.assertTrue(evidence.passed)

    def test_real_numeric_difference_is_source_revision(self) -> None:
        evidence = compare_scope(
            plan=ScopePlan("spot_klines", "BTCUSDT", "1h", "2020-01", ("first",)),
            zip_rows=[row(high="110")],
            rest_rows=[row(high="111")],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        self.assertEqual(evidence.classification_counts["source_revision"], 1)
        self.assertEqual(evidence.differences[0].field, "high")
        self.assertFalse(evidence.passed)

    def test_adjacent_official_scope_can_explain_boundary_row(self) -> None:
        missing = row(3_600_000)
        evidence = compare_scope(
            plan=ScopePlan("spot_klines", "BTCUSDT", "1h", "2020-01", ("gap",)),
            zip_rows=[row(0)],
            rest_rows=[row(0), missing],
            adjacent_zip_rows=[missing],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        self.assertEqual(evidence.classification_counts["boundary_row"], 1)
        self.assertEqual(evidence.classification_counts["timestamp_mismatch"], 0)
        self.assertTrue(evidence.passed)

    def test_supplemental_daily_zip_can_explain_monthly_archive_omission(self) -> None:
        missing = row(3_600_000)
        evidence = compare_scope(
            plan=ScopePlan("um_futures_klines", "BTCUSDT", "1h", "2020-01", ("gap",)),
            zip_rows=[row(0)],
            rest_rows=[row(0), missing],
            supplemental_zip_rows=[missing],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        self.assertEqual(evidence.classification_counts["boundary_row"], 1)
        self.assertEqual(evidence.classification_counts["timestamp_mismatch"], 0)
        self.assertIn("supplemental official daily ZIP", evidence.differences[0].note)
        self.assertTrue(evidence.passed)

    def test_daily_zip_does_not_hide_monthly_source_revision(self) -> None:
        monthly = row(high="110")
        rest = row(high="111")
        evidence = compare_scope(
            plan=ScopePlan("um_futures_klines", "BTCUSDT", "1h", "2020-01", ("anomaly",)),
            zip_rows=[monthly],
            rest_rows=[rest],
            supplemental_zip_rows=[monthly],
            supplemental_zip_statuses={"2020-01-01": "200:none"},
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        self.assertEqual(evidence.classification_counts["source_revision"], 1)
        self.assertIn("monthly and supplemental official daily ZIP agree", evidence.differences[0].note)
        self.assertEqual(evidence.supplemental_zip_statuses, (("2020-01-01", "200:none"),))
        self.assertFalse(evidence.passed)

    def test_unrecovered_timestamp_is_blocking(self) -> None:
        evidence = compare_scope(
            plan=ScopePlan("spot_klines", "BTCUSDT", "1h", "2020-01", ("gap",)),
            zip_rows=[row(0)],
            rest_rows=[row(0), row(3_600_000)],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        self.assertEqual(evidence.classification_counts["timestamp_mismatch"], 1)
        self.assertFalse(evidence.passed)

    def test_invalid_ohlcv_and_negative_volume_block(self) -> None:
        invalid = row(high="90", low="110", volume="-1")
        evidence = compare_scope(
            plan=ScopePlan("spot_klines", "BTCUSDT", "1h", "2020-01", ("anomaly",)),
            zip_rows=[invalid],
            rest_rows=[invalid],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        self.assertGreaterEqual(evidence.classification_counts["invalid_ohlcv"], 1)
        self.assertFalse(evidence.passed)


class DualSourceGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = ScopePlan("spot_klines", "BTCUSDT", "1h", "2020-01", ("first", "middle", "latest_complete"))

    def test_http_451_and_zip_unavailable_are_blocking(self) -> None:
        rest_failure = source_failure(self.plan, "network_blocked", "http_451", rest_http_status=451)
        zip_failure = source_failure(self.plan, "zip_unavailable", "http_404", zip_http_status=404)
        self.assertFalse(rest_failure.passed)
        self.assertFalse(zip_failure.passed)
        self.assertFalse(evaluate_gate([rest_failure], [self.plan]).passed)

    def test_missing_dataset_scope_overlap_or_hash_blocks(self) -> None:
        good = compare_scope(
            plan=self.plan,
            zip_rows=[row()],
            rest_rows=[row()],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        missing_dataset = ScopePlan("spot_klines", "ETHUSDT", "1h", "2020-01", ("first",))
        self.assertFalse(evaluate_gate([good], [self.plan, missing_dataset]).passed)

        no_overlap = compare_scope(
            plan=self.plan,
            zip_rows=[row(0)],
            rest_rows=[row(3_600_000)],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        self.assertFalse(evaluate_gate([no_overlap], [self.plan]).passed)

        missing_hash = compare_scope(
            plan=self.plan,
            zip_rows=[row()],
            rest_rows=[row()],
            zip_payload_sha256="",
            rest_payload_sha256="b" * 64,
        )
        self.assertFalse(evaluate_gate([missing_hash], [self.plan]).passed)

    def test_complete_required_evidence_passes(self) -> None:
        evidence = compare_scope(
            plan=self.plan,
            zip_rows=[row()],
            rest_rows=[row()],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        gate = evaluate_gate([evidence], [self.plan])
        self.assertTrue(gate.passed)
        self.assertEqual(gate.blockers, ())

    def test_comparable_failure_replaces_stale_network_failure_in_gate_detail(self) -> None:
        network_failure = source_failure(self.plan, "network_blocked", "http_451", rest_http_status=451)
        comparable_failure = compare_scope(
            plan=self.plan,
            zip_rows=[row(high="110")],
            rest_rows=[row(high="111")],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
        )
        gate = evaluate_gate([network_failure, comparable_failure], [self.plan])
        self.assertEqual(gate.blockers, (f"{self.plan.key}: source_revision",))

    def test_serialized_report_is_sanitized(self) -> None:
        evidence = compare_scope(
            plan=self.plan,
            zip_rows=[row()],
            rest_rows=[row()],
            zip_payload_sha256="a" * 64,
            rest_payload_sha256="b" * 64,
            supplemental_zip_statuses={
                "2020-01-01": "200:none",
                "2020-01-02": "404:http_404",
            },
        )
        run = AuditRunEvidence(
            execution_label="remote",
            generated_utc="2026-07-10T00:00:00Z",
            plans=(self.plan,),
            scopes=(evidence,),
            transport="direct",
        )
        report = render_diagnostics_report([run])
        forbidden = ("47.97.", "BINANCE_API_KEY", "BINANCE_API_SECRET", "raw payload", "tranId")
        for value in forbidden:
            self.assertNotIn(value, report)
        self.assertIn("- API key used: no", report)
        self.assertIn("- Status: pass", report)
        self.assertIn("`direct`", report)
        revalidation = render_revalidation_report([run])
        self.assertIn("`2020-01-02` | `404:http_404`", revalidation)
        self.assertIn("Supplemental daily ZIP requests unavailable or invalid: 1", revalidation)
        self.assertIn("- Status: pass", revalidation)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            path.write_text(json.dumps(run.to_dict()), encoding="utf-8")
            restored = AuditRunEvidence.from_dict(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(restored.execution_label, "remote")
        self.assertEqual(restored.scopes[0].overlap_rows, 1)


class DualSourceOrchestrationTests(unittest.TestCase):
    def test_profile_scope_contains_first_middle_latest_anomaly_and_gap(self) -> None:
        def timestamp(value: str) -> int:
            return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp() * 1000)

        january = row(timestamp("2020-01-01T00:00:00"))
        february = row(timestamp("2020-02-01T00:00:00"), high="150", low="80")
        march = row(timestamp("2020-03-01T02:00:00"))
        plans = m0_dual_source_audit._select_scope_plans(
            "spot_klines",
            "BTCUSDT",
            "1h",
            {"2020-01": [january], "2020-02": [february], "2020-03": [march]},
            [],
        )
        reasons = {plan.month: set(plan.reasons) for plan in plans}
        self.assertIn("first", reasons["2020-01"])
        self.assertIn("middle", reasons["2020-02"])
        self.assertIn("anomaly", reasons["2020-02"])
        self.assertIn("latest_complete", reasons["2020-03"])
        self.assertTrue(any("gap" in item for item in reasons.values()))

    def test_loopback_proxy_validation_rejects_credentials_and_remote_hosts(self) -> None:
        self.assertEqual(
            m0_dual_source_audit._validated_proxy_url("http://127.0.0.1:10808"),
            "http://127.0.0.1:10808",
        )
        self.assertEqual(
            m0_dual_source_audit._validated_proxy_url("http://localhost:10808"),
            "http://localhost:10808",
        )
        for value in (
            "http://user:password@127.0.0.1:10808",
            "http://192.168.1.10:10808",
            "socks5://127.0.0.1:10808",
        ):
            with self.assertRaises(ValueError):
                m0_dual_source_audit._validated_proxy_url(value)

    def test_public_orchestrator_has_no_credentials_or_trading_calls(self) -> None:
        source = (ROOT / "scripts" / "m0_dual_source_audit.py").read_text(encoding="utf-8")
        for forbidden in (
            "BINANCE_API_KEY",
            "BINANCE_API_SECRET",
            "/api/v3/order",
            "/fapi/v1/order",
            "create_order",
            "cancel_order",
            "place_order",
        ):
            self.assertNotIn(forbidden, source)

        workflow = (ROOT / ".github" / "workflows" / "m0-public-dual-source-audit.yml").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("private", workflow.lower())

    def test_dataset_orchestrator_declares_separate_zip_and_rest_fetchers(self) -> None:
        import inspect

        parameters = inspect.signature(m0_dual_source_audit._run_dataset_symbol).parameters
        self.assertIn("zip_fetcher", parameters)
        self.assertIn("rest_fetcher", parameters)

    def test_daily_zip_url_and_bundle_hash_are_deterministic(self) -> None:
        url = m0_dual_source_audit._daily_zip_url(
            "https://data.binance.vision",
            "mark_price_klines",
            "BTCUSDT",
            "1h",
            "2021-07-01",
        )
        self.assertEqual(
            url,
            "https://data.binance.vision/data/futures/um/daily/markPriceKlines/"
            "BTCUSDT/1h/BTCUSDT-1h-2021-07-01.zip",
        )
        left = m0_dual_source_audit._combined_sha256([("monthly", b"a"), ("daily", b"b")])
        right = m0_dual_source_audit._combined_sha256([("daily", b"b"), ("monthly", b"a")])
        self.assertEqual(left, right)
        self.assertEqual(len(left), 64)


if __name__ == "__main__":
    unittest.main()
