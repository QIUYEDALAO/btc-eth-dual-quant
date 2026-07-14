from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.liquid_universe import (
    DailyEvidence,
    MinuteBar,
    aggregate_one_hour,
    build_month,
    expected_five_minute_grid,
    membership_hash,
    merge_daily,
    validate_symbol_month_grid,
)
from scripts.liquid_universe_public_run import archive_timestamp

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text())
REGISTRY = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text())
SHA = "a" * 64


def daily(symbol: str, day: date, volume: str = "100", *, authority: str = "official_monthly_zip", sha: str = SHA) -> DailyEvidence:
    return DailyEvidence(symbol, day, Decimal(volume), authority, sha, Decimal("1"), Decimal("3"), Decimal("0.5"), Decimal("2"), Decimal("10"))


def evidence(symbol: str, start: date, count: int, volume: str = "100") -> list[DailyEvidence]:
    return [daily(symbol, start + timedelta(days=index), volume) for index in range(count)]


def bar(symbol: str, timestamp: datetime, *, volume: str = "0.1") -> MinuteBar:
    return MinuteBar(symbol, timestamp, Decimal("1"), Decimal("3"), Decimal("0.5"), Decimal("2"), Decimal(volume), Decimal("2"), 1, Decimal("0.05"), Decimal("1"))


class QualificationTests(unittest.TestCase):
    def test_archive_millisecond_and_microsecond_timestamps_match(self):
        self.assertEqual(archive_timestamp("1704067200000"), archive_timestamp("1704067200000000"))

    def test_daily_only_fills_missing_and_conflict_blocks(self):
        day = date(2020, 1, 1)
        monthly = daily("BTCUSDT", day)
        same = daily("BTCUSDT", day, authority="official_daily_zip", sha="b" * 64)
        self.assertEqual(merge_daily([monthly], [same]), [monthly])
        conflict = DailyEvidence("BTCUSDT", day, Decimal("9"), "official_daily_zip", "b" * 64, Decimal("1"), Decimal("3"), Decimal("0.5"), Decimal("2"), Decimal("10"))
        with self.assertRaisesRegex(ValueError, "monthly/daily conflict"):
            merge_daily([monthly], [conflict])
        with self.assertRaisesRegex(ValueError, "duplicate official_monthly_zip"):
            merge_daily([monthly, monthly], [])

    def test_contiguous_history_rank_window_and_tie_break(self):
        effective = date(2021, 1, 1)
        start = effective - timedelta(days=365)
        rows = evidence("ETHUSDT", start, 365) + evidence("BTCUSDT", start, 365)
        result = build_month(effective, rows, CONTRACT, REGISTRY)
        self.assertEqual([row.symbol for row in result], ["BTCUSDT", "ETHUSDT"])
        self.assertEqual(result[0].history_days, 365)
        future = daily("ZZZUSDT", effective, "999999")
        self.assertEqual(result, build_month(effective, rows + [future], CONTRACT, REGISTRY))

    def test_accumulated_365_with_middle_gap_is_rejected(self):
        effective = date(2021, 1, 1)
        start = effective - timedelta(days=366)
        rows = evidence("AAAUSDT", start, 366)
        rows = [row for row in rows if row.day != effective - timedelta(days=100)]
        self.assertEqual(build_month(effective, rows, CONTRACT, REGISTRY), [])

    def test_missing_rank_day_and_short_history_are_rejected(self):
        effective = date(2021, 1, 1)
        start = effective - timedelta(days=365)
        missing_rank = [row for row in evidence("AAAUSDT", start, 365) if row.day != effective - timedelta(days=10)]
        short = evidence("BBBUSDT", start + timedelta(days=1), 364)
        self.assertEqual(build_month(effective, missing_rank + short, CONTRACT, REGISTRY), [])

    def test_median_resists_single_day_spike(self):
        effective = date(2021, 1, 1)
        start = effective - timedelta(days=365)
        first = evidence("AAAUSDT", start, 365)
        first[-1] = daily("AAAUSDT", first[-1].day, "999999")
        rows = first + evidence("BBBUSDT", start, 365, "101")
        self.assertEqual([row.symbol for row in build_month(effective, rows, CONTRACT, REGISTRY)], ["BBBUSDT", "AAAUSDT"])

    def test_invalid_daily_values_block(self):
        effective = date(2021, 1, 1)
        start = effective - timedelta(days=365)
        for value in ("NaN", "Infinity", "-1"):
            rows = evidence("AAAUSDT", start, 365)
            rows[-1] = daily("AAAUSDT", rows[-1].day, value)
            with self.assertRaises(ValueError):
                build_month(effective, rows, CONTRACT, REGISTRY)

    def test_exact_aggregation_checks_symbol_utc_continuity_and_ohlcv(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        bars = [bar("BTCUSDT", start + timedelta(minutes=5 * index)) for index in range(12)]
        aggregate = aggregate_one_hour(bars)
        self.assertEqual(aggregate.volume, Decimal("1.2"))
        self.assertEqual(aggregate.trade_count, 12)
        for changed in (
            bars[:-1],
            bars[:6] + [bar("ETHUSDT", bars[6].open_time)] + bars[7:],
            bars[:5] + [bars[4]] + bars[6:],
        ):
            with self.assertRaises(ValueError):
                aggregate_one_hour(changed)
        naive = list(bars)
        naive[0] = bar("BTCUSDT", naive[0].open_time.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            aggregate_one_hour(naive)

    def test_complete_grid_detects_whole_hour_and_single_slot(self):
        grid = expected_five_minute_grid("2024-02")
        bars = [bar("BTCUSDT", timestamp) for timestamp in grid]
        removed_hour = {datetime(2024, 2, 10, 3, minute, tzinfo=timezone.utc) for minute in range(0, 60, 5)}
        result = validate_symbol_month_grid("BTCUSDT", "2024-02", [item for item in bars if item.open_time not in removed_hour])
        self.assertEqual(set(result.missing), removed_hour)
        result = validate_symbol_month_grid("BTCUSDT", "2024-02", bars[:-1])
        self.assertEqual(len(result.missing), 1)

    def test_grid_rejects_duplicate_off_grid_month_symbol_and_invalid_values(self):
        timestamp = datetime(2024, 2, 1, tzinfo=timezone.utc)
        cases = [
            [bar("BTCUSDT", timestamp), bar("BTCUSDT", timestamp)],
            [bar("BTCUSDT", timestamp + timedelta(minutes=1))],
            [bar("BTCUSDT", datetime(2024, 3, 1, tzinfo=timezone.utc))],
            [bar("ETHUSDT", timestamp)],
            [bar("BTCUSDT", timestamp.replace(tzinfo=None))],
            [MinuteBar("BTCUSDT", timestamp, Decimal("2"), Decimal("1"), Decimal("0"), Decimal("2"), Decimal("1"))],
            [bar("BTCUSDT", timestamp, volume="-1")],
        ]
        for bars in cases:
            self.assertTrue(validate_symbol_month_grid("BTCUSDT", "2024-02", bars).errors)

    def test_membership_hash_is_order_independent_and_content_sensitive(self):
        effective = date(2021, 1, 1)
        start = effective - timedelta(days=365)
        rows = build_month(effective, evidence("BTCUSDT", start, 365) + evidence("ETHUSDT", start, 365), CONTRACT, REGISTRY)
        self.assertEqual(membership_hash(rows), membership_hash(list(reversed(rows))))
        changed = build_month(effective, evidence("BTCUSDT", start, 365, "101") + evidence("ETHUSDT", start, 365), CONTRACT, REGISTRY)
        self.assertNotEqual(membership_hash(rows), membership_hash(changed))


if __name__ == "__main__":
    unittest.main()
