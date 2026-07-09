from __future__ import annotations

import inspect
import json
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from btc_eth_dual_quant.backtest.skeleton import (
    LookaheadBiasError,
    MarketBar,
    assert_feature_available,
    schedule_next_open,
)
from btc_eth_dual_quant.backtest.m0_data import M0DataIndexError, load_funding_records
from btc_eth_dual_quant.data import binance
from btc_eth_dual_quant.data.binance import BinanceClientError, BinanceReadOnlyRestClient
from btc_eth_dual_quant.data.costs import (
    compute_roundtrip_cost,
    funding_payback_threshold,
    parse_futures_commission,
    parse_spot_commission,
)
from btc_eth_dual_quant.data.funding import annualize_funding_rate, infer_funding_interval_hours
from btc_eth_dual_quant.data.quality import (
    audit_zip_rest_klines,
    compare_zip_rest_klines,
    detect_kline_gaps,
    flag_kline_anomalies,
    missing_archive_days,
)
from btc_eth_dual_quant.data.registry import load_registry
from btc_eth_dual_quant.data.storage import AppendOnlyRawStore
from btc_eth_dual_quant.data.duckdb_layer import DuckDBLayer


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from m0_report import DatasetRun, M0RunReport, _required_checks_complete, parse_report, write_report
from m0_anomaly_review import CROSS_ENDPOINT_MARKET_MOVE_NOTE, review_anomaly, write_review
from m0_anomaly_review import ReviewedAnomaly
import m0_report_merge
import m0_audit_revalidate
import m0_backfill_public
from m0_smoke_readonly_private import write_private_status


class RegistryTests(unittest.TestCase):
    def test_registry_covers_all_v1_1_table_9_items(self) -> None:
        registry = load_registry(ROOT / "data_registry.yaml")
        self.assertEqual(len(registry.datasets), 20)
        required = {
            "name",
            "source",
            "endpoint",
            "fields",
            "granularity",
            "history_start",
            "retention_limit",
            "update_freq",
            "table",
            "validations",
            "fallback",
            "consumers",
        }
        for record in registry.datasets:
            dumped = record.model_dump()
            self.assertTrue(required.issubset(dumped.keys()))

    def test_m0_enabled_records_match_requested_collectors(self) -> None:
        enabled = {record.name for record in load_registry(ROOT / "data_registry.yaml").enabled_records()}
        self.assertEqual(
            enabled,
            {
                "spot_klines",
                "um_futures_klines",
                "funding_rate_history",
                "premium_index",
                "funding_info",
                "mark_price_klines",
                "index_price_klines",
                "premium_index_klines",
                "open_interest",
                "order_book_depth",
                "funding_income",
                "commissions",
                "exchange_rules",
            },
        )


class StorageAndCollectorTests(unittest.TestCase):
    def test_raw_store_is_append_only_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AppendOnlyRawStore(tmp)
            store.append("spot_klines", "test", "GET /api/v3/klines", {"symbol": "BTCUSDT"}, [[1]])
            store.append("spot_klines", "test", "GET /api/v3/klines", {"symbol": "BTCUSDT"}, [[2]])
            records = store.iter_envelopes("spot_klines")
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].payload, [[1]])
            self.assertEqual(records[1].payload, [[2]])

    def test_client_rejects_trading_paths(self) -> None:
        with self.assertRaises(BinanceClientError):
            BinanceReadOnlyRestClient._assert_read_only("/api/v3/order")
        with self.assertRaises(BinanceClientError):
            BinanceReadOnlyRestClient._assert_read_only("/fapi/v1/countdownCancelAll")

    def test_raw_store_rejects_path_traversal_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AppendOnlyRawStore(tmp)
            with self.assertRaises(ValueError):
                store.append("../escape", "fixture", "GET /public", {}, [])

    def test_duckdb_insert_count_and_identifier_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AppendOnlyRawStore(Path(tmp) / "raw")
            first = store.append("spot_klines", "fixture", "GET /public", {}, [[1]])
            db = DuckDBLayer(Path(tmp) / "m0.duckdb")
            self.assertEqual(db.index_envelopes([first]), 1)
            self.assertEqual(db.index_envelopes([first]), 0)
            with self.assertRaises(ValueError):
                db.create_derived_table('bad"table', [{"value": 1}])


class FundingTests(unittest.TestCase):
    def test_funding_info_has_priority_when_consistent(self) -> None:
        result = infer_funding_interval_hours(
            "BTCUSDT",
            funding_info={"symbol": "BTCUSDT", "fundingIntervalHours": 4},
            premium_index={"symbol": "BTCUSDT", "time": 0, "nextFundingTime": 14_400_000},
            funding_rate_history=[
                {"symbol": "BTCUSDT", "fundingTime": 0},
                {"symbol": "BTCUSDT", "fundingTime": 14_400_000},
            ],
        )
        self.assertEqual(result.hours, Decimal("4"))
        self.assertEqual(result.source, "fundingInfo.fundingIntervalHours")
        self.assertEqual(result.warnings, [])

    def test_conflict_uses_shorter_interval_and_warns(self) -> None:
        result = infer_funding_interval_hours(
            "BTCUSDT",
            funding_info={"symbol": "BTCUSDT", "fundingIntervalHours": 8},
            premium_index=[
                {"symbol": "BTCUSDT", "time": 0, "nextFundingTime": 14_400_000},
                {"symbol": "BTCUSDT", "time": 1, "nextFundingTime": 28_800_000},
            ],
        )
        self.assertEqual(result.hours, Decimal("4"))
        self.assertEqual(result.source, "conflict_shorter_interval")
        self.assertTrue(result.warnings)

    def test_premium_index_fallback(self) -> None:
        result = infer_funding_interval_hours(
            "BTCUSDT",
            premium_index=[
                {"symbol": "BTCUSDT", "time": 1000, "nextFundingTime": 14_401_000},
                {"symbol": "BTCUSDT", "time": 2000, "nextFundingTime": 28_801_000},
            ],
        )
        self.assertEqual(result.hours, Decimal("4"))
        self.assertEqual(result.source, "premiumIndex.nextFundingTime")

    def test_single_premium_snapshot_is_not_a_complete_interval(self) -> None:
        with self.assertRaises(ValueError):
            infer_funding_interval_hours(
                "BTCUSDT",
                premium_index={"symbol": "BTCUSDT", "time": 1000, "nextFundingTime": 14_401_000},
            )

    def test_history_preserves_variable_event_intervals(self) -> None:
        result = infer_funding_interval_hours(
            "BTCUSDT",
            funding_rate_history=[
                {"symbol": "BTCUSDT", "fundingTime": 0},
                {"symbol": "BTCUSDT", "fundingTime": 14_400_000},
                {"symbol": "BTCUSDT", "fundingTime": 36_000_000},
                {"symbol": "BTCUSDT", "fundingTime": 64_800_000},
                {"symbol": "BTCUSDT", "fundingTime": 108_000_000},
            ],
        )
        self.assertEqual(
            list(result.event_intervals.values()),
            [Decimal("4"), Decimal("4"), Decimal("6"), Decimal("8"), Decimal("12")],
        )

    def test_history_fallback_and_annualization(self) -> None:
        result = infer_funding_interval_hours(
            "ETHUSDT",
            funding_rate_history=[
                {"symbol": "ETHUSDT", "fundingTime": 0},
                {"symbol": "ETHUSDT", "fundingTime": 21_600_000},
                {"symbol": "ETHUSDT", "fundingTime": 43_200_000},
            ],
        )
        self.assertEqual(result.hours, Decimal("6"))
        self.assertEqual(annualize_funding_rate("0.001", result.hours), Decimal("1.460"))

    def test_m0_loader_preserves_interval_per_funding_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            AppendOnlyRawStore(root / "raw").append(
                "funding_rate_history",
                "fixture",
                "GET public funding history",
                {"symbol": "BTCUSDT"},
                [
                    {"symbol": "BTCUSDT", "fundingTime": 0, "fundingRate": "0.001"},
                    {"symbol": "BTCUSDT", "fundingTime": 14_400_000, "fundingRate": "0.001"},
                    {"symbol": "BTCUSDT", "fundingTime": 36_000_000, "fundingRate": "0.001"},
                ],
            )
            records = load_funding_records(
                "BTCUSDT",
                raw_root=root / "raw",
                duckdb_path=root / "missing.duckdb",
            )
        self.assertEqual([record.interval_hours for record in records], [4.0, 4.0, 6.0])
        self.assertAlmostEqual(records[-1].annualized_rate, 1.46)

    def test_existing_broken_duckdb_does_not_silently_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "broken.duckdb").write_text("not a database", encoding="utf-8")
            AppendOnlyRawStore(root / "raw").append(
                "funding_rate_history",
                "fixture",
                "GET public funding history",
                {"symbol": "BTCUSDT"},
                [
                    {"symbol": "BTCUSDT", "fundingTime": 0, "fundingRate": "0.001"},
                    {"symbol": "BTCUSDT", "fundingTime": 14_400_000, "fundingRate": "0.001"},
                ],
            )
            with self.assertRaises(M0DataIndexError):
                load_funding_records(
                    "BTCUSDT",
                    raw_root=root / "raw",
                    duckdb_path=root / "broken.duckdb",
                )


class CostTests(unittest.TestCase):
    def test_parse_commissions_and_roundtrip_cost(self) -> None:
        spot = parse_spot_commission(
            {"standardCommission": {"maker": "0.001", "taker": "0.001"}, "discount": {"discount": "0.25"}}
        )
        futures = parse_futures_commission({"makerCommissionRate": "0.0002", "takerCommissionRate": "0.0005"})
        cost = compute_roundtrip_cost(spot.taker, futures.taker, "0.0005")
        self.assertEqual(futures.taker, Decimal("0.0005"))
        self.assertEqual(cost.total_rate, Decimal("0.0050"))

    def test_payback_threshold(self) -> None:
        result = funding_payback_threshold("0.20", 14, "0.005", "2.0")
        self.assertEqual(result.expected_funding_income_rate, Decimal("0.007671232876712328767123287672"))
        self.assertFalse(result.passes)
        self.assertTrue(funding_payback_threshold("0.40", 14, "0.005", "2.0").passes)


class QualityTests(unittest.TestCase):
    def test_gap_detection_blocks_only_over_three_missing_bars(self) -> None:
        rows = [{"open_time": 0}, {"open_time": 60_000}, {"open_time": 5 * 60_000}]
        report = detect_kline_gaps(rows, "1m")
        self.assertEqual(report.gaps[0].missing_count, 3)
        self.assertFalse(report.blocks_backtest)
        rows.append({"open_time": 10 * 60_000})
        self.assertTrue(detect_kline_gaps(rows, "1m").blocks_backtest)

    def test_zip_rest_compare_and_anomaly_flags(self) -> None:
        left = [{"open_time": 1, "open": "100", "high": "110", "low": "90", "close": "100", "volume": "10", "quote_volume": "1000"}]
        right = [{"open_time": 1, "open": "100.2", "high": "110", "low": "90", "close": "100", "volume": "10", "quote_volume": "1000"}]
        self.assertEqual(compare_zip_rest_klines(left, right)[0].field, "open")
        audit = audit_zip_rest_klines(left, left)
        self.assertEqual(audit.overlap_rows, 1)
        self.assertEqual(audit.differences, [])
        self.assertEqual(len(audit.rest_payload_sha256), 64)
        self.assertEqual(len(audit.zip_payload_sha256), 64)
        anomalies = flag_kline_anomalies(
            [{"open_time": 1, "open": "100", "high": "140", "low": "90", "close": "100", "volume": "0"}]
        )
        self.assertEqual({item.reason for item in anomalies}, {"amplitude_gt_30pct", "zero_volume"})

    def test_zip_rest_scope_covers_first_middle_latest_and_anomalies(self) -> None:
        rows = [
            {"open_time": 1_577_836_800_000, "open": "100", "high": "101", "low": "99", "volume": "1"},
            {"open_time": 1_580_515_200_000, "open": "100", "high": "150", "low": "90", "volume": "1"},
            {"open_time": 1_583_020_800_000, "open": "100", "high": "101", "low": "99", "volume": "1"},
        ]
        months, scope = m0_backfill_public._audit_months("spot_klines", rows)
        self.assertEqual([month.isoformat()[:7] for month in months], ["2020-01", "2020-02", "2020-03"])
        self.assertEqual(
            scope,
            "first=2020-01;middle=2020-02;latest_complete=2020-03;anomaly=2020-02",
        )

    def test_archive_completeness_missing_days(self) -> None:
        records = [{"time": 0}, {"time": 2 * 24 * 60 * 60 * 1000}]
        self.assertEqual(missing_archive_days(records, "time", "1970-01-01", "1970-01-03"), ["1970-01-02"])


class BacktestTimeSemanticsTests(unittest.TestCase):
    def test_decision_schedules_next_bar_open(self) -> None:
        bars = [
            MarketBar(0, 59_999, "1", "2", "1", "2"),
            MarketBar(60_000, 119_999, "2", "3", "2", "3"),
        ]
        decision = schedule_next_open(bars, 0, "signal_after_close")
        self.assertEqual(decision.decision_time_ms, 59_999)
        self.assertEqual(decision.earliest_effective_time_ms, 60_000)

    def test_feature_after_decision_is_lookahead(self) -> None:
        with self.assertRaises(LookaheadBiasError):
            assert_feature_available(100, 99)
        with self.assertRaises(LookaheadBiasError):
            schedule_next_open([MarketBar(0, 1, "1", "1", "1", "1")], 0, "no_next_bar")

    def test_current_bar_close_fill_is_rejected(self) -> None:
        bars = [
            MarketBar(0, 59_999, "1", "2", "1", "2"),
            MarketBar(59_999, 119_999, "2", "3", "2", "3"),
        ]
        with self.assertRaises(LookaheadBiasError):
            schedule_next_open(bars, 0, "same_close_fill")


class M0GuardrailTests(unittest.TestCase):
    def test_no_execution_live_tree_created(self) -> None:
        self.assertFalse((ROOT / "execution" / "live").exists())
        self.assertFalse((ROOT / "src" / "execution" / "live").exists())
        self.assertFalse((ROOT / "src" / "btc_eth_dual_quant" / "execution").exists())

    def test_no_trading_endpoint_implementation(self) -> None:
        source = inspect.getsource(binance)
        forbidden_literals = [
            '"/api/v3/order"',
            '"/fapi/v1/order"',
            "POST",
            "DELETE",
            "place_order",
            "cancel_order",
            "simulate_fill",
            "matching_engine",
        ]
        for literal in forbidden_literals:
            self.assertNotIn(literal, source)


class M0ReportTests(unittest.TestCase):
    def _public_full_history_runs(self) -> list[DatasetRun]:
        runs: list[DatasetRun] = []
        for symbol in ("BTCUSDT", "ETHUSDT"):
            for name in (
                "spot_klines",
                "um_futures_klines",
                "mark_price_klines",
                "index_price_klines",
                "premium_index_klines",
                "funding_rate_history",
            ):
                runs.append(
                    DatasetRun(
                        name=f"{name}:{symbol}",
                        interval="1d",
                        rows=1,
                        start_ms=0,
                        end_ms=86_399_999,
                        zip_rest_differences=0,
                        zip_rest_overlap=1,
                        rest_payload_sha256="a" * 64,
                        zip_payload_sha256="a" * 64,
                        zip_rest_scope="first=2020-01;middle=2021-01;latest_complete=2022-01;anomaly=none",
                        funding_interval_warnings="not_applicable",
                        archive_status="not_applicable",
                        commission_status="not_applicable",
                    )
                )
            runs.append(
                DatasetRun(
                    name=f"funding_interval_{symbol}",
                    interval="inferred",
                    rows=1,
                    start_ms=0,
                    end_ms=0,
                    zip_rest_differences="not_applicable",
                    funding_interval_warnings=0,
                    archive_status="not_applicable",
                    commission_status="not_applicable",
                )
            )
            runs.append(
                DatasetRun(
                    name=f"open_interest:{symbol}",
                    interval="1d",
                    rows=1,
                    start_ms=0,
                    end_ms=0,
                    zip_rest_differences="not_applicable",
                    funding_interval_warnings="not_applicable",
                    archive_status="pass_retention_limited",
                    commission_status="not_applicable",
                )
            )
        return runs

    def test_report_defaults_do_not_share_final_data_run_path(self) -> None:
        self.assertIn('default="reports/m0/M0_PUBLIC_RUN_REPORT.md"', (ROOT / "scripts" / "m0_backfill_public.py").read_text())
        self.assertIn(
            'default="reports/m0/M0_PRIVATE_SMOKE_REPORT.local.md"',
            (ROOT / "scripts" / "m0_smoke_readonly_private.py").read_text(),
        )
        self.assertIn(
            'default="reports/m0/M0_SCHEDULER_DRY_RUN_REPORT.md"',
            (ROOT / "scripts" / "m0_scheduler_dry_run.py").read_text(),
        )

    def test_required_checks_block_when_zip_rest_was_not_run(self) -> None:
        run = DatasetRun(
            name="spot_klines:BTCUSDT",
            interval="1h",
            rows=10,
            zip_rest_differences="not_run",
            funding_interval_warnings="not_applicable",
            archive_status="not_applicable",
            commission_status="not_applicable",
        )
        self.assertFalse(_required_checks_complete([run]))

    def test_render_cannot_override_failed_dataset_checks(self) -> None:
        run = DatasetRun(
            name="spot_klines:BTCUSDT",
            interval="1h",
            rows=10,
            zip_rest_differences="not_run",
            funding_interval_warnings="not_applicable",
            archive_status="not_applicable",
            commission_status="not_applicable",
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "report.md"
            write_report(
                M0RunReport(
                    data_start="2026-01-01",
                    data_end="2026-01-02",
                    datasets=[run],
                    public_full_history_complete=True,
                    required_checks_complete=True,
                ),
                output,
            )
            text = output.read_text(encoding="utf-8")
        self.assertIn("- Public full-history: `blocked`", text)
        self.assertIn("- Required checks: `blocked`", text)

    def test_m0_audit_revalidation_passes_complete_1h_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_root = root / "raw"
            store = AppendOnlyRawStore(raw_root)
            runs: list[DatasetRun] = []
            for symbol in ("BTCUSDT", "ETHUSDT"):
                for name in (
                    "spot_klines",
                    "um_futures_klines",
                    "mark_price_klines",
                    "index_price_klines",
                    "premium_index_klines",
                ):
                    runs.append(
                        DatasetRun(
                            name=f"{name}:{symbol}",
                            interval="1h",
                            rows=100,
                            gaps=0,
                            zip_rest_differences=0,
                            zip_rest_overlap=72,
                            rest_payload_sha256="a" * 64,
                            zip_payload_sha256="b" * 64,
                            zip_rest_scope=(
                                "first=2020-01;middle=2021-01;latest_complete=2022-01;anomaly=none"
                            ),
                            funding_interval_warnings="not_applicable",
                            archive_status="not_applicable",
                            commission_status="not_applicable",
                        )
                    )
                runs.append(
                    DatasetRun(
                        name=f"funding_rate_history:{symbol}",
                        interval="funding_period",
                        rows=3,
                        funding_interval_warnings="not_applicable",
                        archive_status="not_applicable",
                        commission_status="not_applicable",
                        zip_rest_differences="not_applicable",
                    )
                )
                store.append(
                    "funding_rate_history",
                    "fixture",
                    "GET public funding history",
                    {"symbol": symbol},
                    [
                        {"symbol": symbol, "fundingTime": 0, "fundingRate": "0.0001"},
                        {"symbol": symbol, "fundingTime": 14_400_000, "fundingRate": "0.0001"},
                        {"symbol": symbol, "fundingTime": 43_200_000, "fundingRate": "0.0001"},
                    ],
                )
            report = M0RunReport(data_start="2020-01-01", data_end="2022-01-31", datasets=runs)
            text, passed = m0_audit_revalidate.render_audit_report(report, raw_root)
        self.assertTrue(passed)
        self.assertIn("- Status: pass", text)
        self.assertIn("4h=2, 8h=1", text)

    def test_m0_audit_revalidation_blocks_missing_zip_evidence(self) -> None:
        report = M0RunReport(
            data_start="2020-01-01",
            data_end="2020-01-02",
            datasets=[DatasetRun(name="spot_klines:BTCUSDT", interval="1h", rows=24)],
        )
        with tempfile.TemporaryDirectory() as tmp:
            text, passed = m0_audit_revalidate.render_audit_report(report, Path(tmp) / "raw")
        self.assertFalse(passed)
        self.assertIn("- Status: blocked", text)
        self.assertIn("ZIP/REST fields equal", text)

    def test_merge_hides_private_details_and_keeps_m1_gate_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            public = root / "public.md"
            scheduler = root / "scheduler.md"
            private = root / "private.local.md"
            output = root / "merged.md"
            write_report(
                M0RunReport(data_start="2019-09-01T00:00:00+00:00", data_end="2026-07-09T00:00:00+00:00", datasets=self._public_full_history_runs()),
                public,
            )
            write_report(
                M0RunReport(
                    data_start="scheduler_dry_run",
                    data_end="2026-07-09T00:00:00+00:00",
                    scheduler_dry_run=["daily 00:10 UTC oi_daily_archive"],
                    scheduler_dry_run_complete=True,
                ),
                scheduler,
            )
            write_report(
                M0RunReport(
                    data_start="private_smoke",
                    data_end="private_smoke",
                    private_smoke=["BTCUSDT spot commission taker=0.001 maker=0.001"],
                    private_smoke_complete=True,
                ),
                private,
            )
            old_argv = sys.argv
            try:
                sys.argv = [
                    "m0_report_merge.py",
                    "--public-report",
                    str(public),
                    "--scheduler-report",
                    str(scheduler),
                    "--anomaly-review",
                    str(root / "missing_review.md"),
                    "--private-status-file",
                    str(root / "missing_status.md"),
                    "--private-report",
                    str(private),
                    "--output",
                    str(output),
                ]
                self.assertEqual(m0_report_merge.main(), 0)
            finally:
                sys.argv = old_argv

            text = output.read_text(encoding="utf-8")
            self.assertIn("## Public Full-history Pull Summary", text)
            self.assertIn("- status=pass", text)
            self.assertNotIn("spot commission taker", text)
            self.assertIn("- Public full-history: `pass`", text)
            self.assertIn("- Scheduler dry-run: `pass`", text)
            self.assertIn("- Private read-only smoke: `pass`", text)
            self.assertIn("- Required checks: `pass`", text)
            self.assertIn("- Zero unexplained anomalies: `pass`", text)
            self.assertIn("- Status: `pass`", text)
            parsed = parse_report(output)
            self.assertTrue(parsed.public_full_history_complete)
            self.assertTrue(parsed.scheduler_dry_run_complete)
            self.assertTrue(parsed.private_smoke_complete)

    def test_private_status_file_is_sanitized_and_merge_reads_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            public = root / "public.md"
            scheduler = root / "scheduler.md"
            status = root / "private_status.md"
            output = root / "merged.md"
            write_report(
                M0RunReport(data_start="2019-09-01", data_end="2026-07-09", datasets=self._public_full_history_runs()),
                public,
            )
            write_report(
                M0RunReport(
                    data_start="scheduler_dry_run",
                    data_end="2026-07-09",
                    scheduler_dry_run=["daily 00:10 UTC oi_daily_archive"],
                    scheduler_dry_run_complete=True,
                ),
                scheduler,
            )
            write_private_status(
                status,
                "not_run",
                ["GET /api/v3/account/commission", "GET /fapi/v1/commissionRate", "GET /fapi/v1/income"],
                0,
                0,
            )
            status_text = status.read_text(encoding="utf-8")
            allowed_prefixes = {
                "# M0 Private Smoke Status",
                "",
                "run_status:",
                "endpoints_checked:",
                "- GET /api/v3/account/commission",
                "- GET /fapi/v1/commissionRate",
                "- GET /fapi/v1/income",
                "rows_count:",
                "missing_fields_count:",
                "generated_utc:",
            }
            for line in status_text.splitlines():
                self.assertTrue(any(line.startswith(prefix) for prefix in allowed_prefixes), line)
            forbidden = ["API_KEY", "API_SECRET", "secret", "balance", "tranId", "payload", "income="]
            for item in forbidden:
                self.assertNotIn(item, status_text)

            old_argv = sys.argv
            try:
                sys.argv = [
                    "m0_report_merge.py",
                    "--public",
                    str(public),
                    "--scheduler",
                    str(scheduler),
                    "--anomaly-review",
                    str(root / "missing_review.md"),
                    "--private-status-file",
                    str(status),
                    "--out",
                    str(output),
                ]
                self.assertEqual(m0_report_merge.main(), 0)
            finally:
                sys.argv = old_argv
            merged = output.read_text(encoding="utf-8")
            self.assertIn("- status=not_run", merged)
            self.assertIn("- Private read-only smoke: `blocked`", merged)

    def test_merge_accepts_multiple_public_reports_and_deduplicates_by_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spot = root / "spot.md"
            futures = root / "futures.md"
            scheduler = root / "scheduler.md"
            output = root / "merged.md"
            spot_runs = [
                DatasetRun(
                    name=f"spot_klines:{symbol}",
                    interval="1d",
                    rows=100,
                    start_ms=0,
                    end_ms=99,
                    zip_rest_differences=0,
                    zip_rest_overlap=1,
                    rest_payload_sha256="a" * 64,
                    zip_payload_sha256="a" * 64,
                    zip_rest_scope="first=2020-01;middle=2021-01;latest_complete=2022-01;anomaly=none",
                    funding_interval_warnings="not_applicable",
                    archive_status="not_applicable",
                    commission_status="not_applicable",
                )
                for symbol in ("BTCUSDT", "ETHUSDT")
            ]
            futures_runs = self._public_full_history_runs()
            for dataset in futures_runs:
                if dataset.name.startswith("spot_klines:"):
                    dataset.rows = 10
            write_report(M0RunReport(data_start="2017-08-17", data_end="2026-07-08", datasets=spot_runs), spot)
            write_report(M0RunReport(data_start="2019-09-01", data_end="2026-07-08", datasets=futures_runs), futures)
            write_report(
                M0RunReport(
                    data_start="scheduler_dry_run",
                    data_end="2026-07-09",
                    scheduler_dry_run=["daily 00:10 UTC oi_daily_archive"],
                    scheduler_dry_run_complete=True,
                ),
                scheduler,
            )
            old_argv = sys.argv
            try:
                sys.argv = [
                    "m0_report_merge.py",
                    "--public",
                    str(spot),
                    "--public",
                    str(futures),
                    "--scheduler",
                    str(scheduler),
                    "--anomaly-review",
                    str(root / "missing_review.md"),
                    "--private-status",
                    "pass",
                    "--out",
                    str(output),
                ]
                self.assertEqual(m0_report_merge.main(), 0)
            finally:
                sys.argv = old_argv

            text = output.read_text(encoding="utf-8")
            self.assertEqual(text.count("`spot_klines:BTCUSDT`"), 1)
            self.assertIn("| `spot_klines:BTCUSDT` | `1d` | 100 |", text)
            self.assertIn("`um_futures_klines:BTCUSDT`", text)
            self.assertIn("`funding_interval_ETHUSDT`", text)
            self.assertIn("- Public full-history: `pass`", text)

    def test_anomaly_review_classifies_matching_zip_market_move(self) -> None:
        row = {
            "open_time": 0,
            "open": "100",
            "high": "140",
            "low": "90",
            "close": "120",
            "volume": "10",
        }
        reviewed = review_anomaly(
            "spot_klines",
            "BTCUSDT",
            "1d",
            row,
            "amplitude_gt_30pct",
            "abc123",
            1,
            zip_fetcher=lambda *_args: dict(row),
        )
        self.assertEqual(reviewed.classification, "explained_market_move")
        self.assertTrue(reviewed.zip_available)
        self.assertEqual(reviewed.zip_rest_consistent, "yes")

    def test_anomaly_review_explains_zip_unavailable_with_cross_endpoint_confirmation(self) -> None:
        row = {
            "open_time": 1584057600000,
            "open": "200",
            "high": "205",
            "low": "100",
            "close": "110",
            "volume": "0",
        }
        spot_row = {
            "open_time": 1584057600000,
            "open": "200",
            "high": "206",
            "low": "99",
            "close": "111",
            "volume": "1000",
        }
        futures_row = {
            "open_time": 1584057600000,
            "open": "201",
            "high": "207",
            "low": "98",
            "close": "112",
            "volume": "2000",
        }
        reviewed = review_anomaly(
            "index_price_klines",
            "ETHUSDT",
            "1d",
            row,
            "amplitude_gt_30pct",
            "abc123",
            1,
            zip_fetcher=lambda *_args: None,
            corroborating_rows={
                "spot_klines": spot_row,
                "um_futures_klines": futures_row,
            },
        )
        self.assertEqual(reviewed.classification, "explained_market_move")
        self.assertFalse(reviewed.zip_available)
        self.assertEqual(reviewed.zip_rest_consistent, "not_available")
        self.assertEqual(reviewed.note, CROSS_ENDPOINT_MARKET_MOVE_NOTE)

    def test_anomaly_review_keeps_zip_unavailable_without_corroboration_unresolved(self) -> None:
        row = {
            "open_time": 1584057600000,
            "open": "200",
            "high": "205",
            "low": "100",
            "close": "110",
            "volume": "0",
        }
        spot_row = {
            "open_time": 1584057600000,
            "open": "200",
            "high": "206",
            "low": "99",
            "close": "111",
            "volume": "1000",
        }
        reviewed = review_anomaly(
            "index_price_klines",
            "ETHUSDT",
            "1d",
            row,
            "amplitude_gt_30pct",
            "abc123",
            1,
            zip_fetcher=lambda *_args: None,
            corroborating_rows={"spot_klines": spot_row},
        )
        self.assertEqual(reviewed.classification, "unresolved")
        self.assertFalse(reviewed.zip_available)
        self.assertEqual(reviewed.zip_rest_consistent, "not_available")

    def test_merge_counts_only_unresolved_anomaly_review_as_unexplained(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            public = root / "public.md"
            scheduler = root / "scheduler.md"
            review = root / "review.md"
            output = root / "merged.md"
            runs = self._public_full_history_runs()
            runs[0].kline_anomalies = 2
            runs[0].unexplained = ["kline anomalies pending review: {'amplitude_gt_30pct': 2}"]
            write_report(M0RunReport(data_start="2019-09-01", data_end="2026-07-09", datasets=runs), public)
            write_report(
                M0RunReport(
                    data_start="scheduler_dry_run",
                    data_end="2026-07-09",
                    scheduler_dry_run=["daily 00:10 UTC oi_daily_archive"],
                    scheduler_dry_run_complete=True,
                ),
                scheduler,
            )
            write_review(
                [
                    ReviewedAnomaly(
                        dataset="spot_klines",
                        symbol="BTCUSDT",
                        open_time_utc="1970-01-01T00:00:00+00:00",
                        open="100",
                        high="140",
                        low="90",
                        close="120",
                        volume="10",
                        amplitude="0.50000000",
                        reason="amplitude_gt_30pct",
                        rest_payload_hash="hash1",
                        zip_available=True,
                        zip_rest_consistent="yes",
                        classification="explained_market_move",
                        note="confirmed",
                    ),
                    ReviewedAnomaly(
                        dataset="spot_klines",
                        symbol="BTCUSDT",
                        open_time_utc="1970-01-02T00:00:00+00:00",
                        open="100",
                        high="140",
                        low="90",
                        close="120",
                        volume="10",
                        amplitude="0.50000000",
                        reason="amplitude_gt_30pct",
                        rest_payload_hash="hash2",
                        zip_available=False,
                        zip_rest_consistent="not_available",
                        classification="unresolved",
                        note="missing zip",
                    ),
                ],
                review,
            )
            old_argv = sys.argv
            try:
                sys.argv = [
                    "m0_report_merge.py",
                    "--public-report",
                    str(public),
                    "--scheduler-report",
                    str(scheduler),
                    "--anomaly-review",
                    str(review),
                    "--private-status",
                    "pass",
                    "--output",
                    str(output),
                ]
                self.assertEqual(m0_report_merge.main(), 0)
            finally:
                sys.argv = old_argv

            text = output.read_text(encoding="utf-8")
            self.assertIn("explained_market_move=1", text)
            self.assertIn("unresolved=1", text)
            self.assertIn("- Zero unexplained anomalies: `blocked`", text)
            self.assertIn("- Status: `blocked`", text)


if __name__ == "__main__":
    unittest.main()
