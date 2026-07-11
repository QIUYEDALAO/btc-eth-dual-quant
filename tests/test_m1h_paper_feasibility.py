from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from btc_eth_dual_quant.audit.m1h_paper import (
    FIVE_MINUTE_MS,
    FundingPoint,
    SpotBar,
    expected_reference_time,
    identify_extremes,
    observe_events,
    prior_funding_threshold,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads((ROOT / "config/m1h_is_paper_protocol.json").read_text(encoding="utf-8"))


def ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def history_and_event(symbol: str = "BTCUSDT") -> tuple[list[FundingPoint], FundingPoint]:
    event_time = datetime(2022, 1, 2, tzinfo=timezone.utc)
    points = []
    for offset in range(365, 0, -1):
        timestamp = ms(event_time - timedelta(days=offset))
        points.append(FundingPoint(symbol, timestamp, "0.001", "24", "a" * 64))
    event = FundingPoint(symbol, ms(event_time), "-0.010", "24", "a" * 64)
    points.append(event)
    return points, event


def bars(symbol: str, reference_time: int, count: int = 288) -> tuple[SpotBar, ...]:
    result = []
    for index in range(count):
        opened = reference_time + index * FIVE_MINUTE_MS
        price = Decimal("100") + Decimal(index) / Decimal("100")
        result.append(SpotBar(
            symbol=symbol,
            open_time_ms=opened,
            close_time_ms=opened + FIVE_MINUTE_MS - 1,
            open=str(price),
            high=str(price + Decimal("0.2")),
            low=str(price - Decimal("0.2")),
            close=str(price + Decimal("0.1")),
        ))
    return tuple(result)


class M1HPaperFeasibilityTests(unittest.TestCase):
    def test_current_event_is_excluded_from_rolling_threshold(self) -> None:
        points, event = history_and_event()
        threshold = prior_funding_threshold(points, event, days=365, probability=Decimal("0.05"))
        self.assertEqual(threshold, Decimal("0.365"))
        representatives, raw = identify_extremes(points, PROTOCOL)
        self.assertEqual(raw, 1)
        self.assertEqual(representatives, [event])

    def test_reference_is_strict_next_canonical_five_minute_open(self) -> None:
        exact = ms(datetime(2022, 1, 2, tzinfo=timezone.utc))
        self.assertEqual(expected_reference_time(exact), exact + FIVE_MINUTE_MS)
        self.assertEqual(expected_reference_time(exact + 2), exact + FIVE_MINUTE_MS)

    def test_same_timestamp_bar_is_never_used(self) -> None:
        points, event = history_and_event()
        same_time = SpotBar(event.symbol, event.funding_time_ms, event.funding_time_ms + FIVE_MINUTE_MS - 1, "1", "1", "1", "1")
        later = bars(event.symbol, expected_reference_time(event.funding_time_ms))
        result = observe_events(symbol=event.symbol, points=points, bars=(same_time, *later), protocol=PROTOCOL)
        self.assertEqual(result.complete_events[0].reference_time_ms, expected_reference_time(event.funding_time_ms))

    def test_missing_expected_reference_does_not_search_later_price(self) -> None:
        points, event = history_and_event()
        reference = expected_reference_time(event.funding_time_ms)
        later = bars(event.symbol, reference + FIVE_MINUTE_MS)
        result = observe_events(symbol=event.symbol, points=points, bars=later, protocol=PROTOCOL)
        self.assertEqual(result.invalid_observations, 1)
        self.assertEqual(result.complete_events, ())

    def test_frozen_horizons_mae_mfe_and_recovery_are_path_only(self) -> None:
        points, event = history_and_event()
        reference = expected_reference_time(event.funding_time_ms)
        result = observe_events(symbol=event.symbol, points=points, bars=bars(event.symbol, reference), protocol=PROTOCOL)
        observed = result.complete_events[0]
        self.assertEqual(tuple(horizon for horizon, _ in observed.horizon_displacements), (1, 2, 4, 8, 12, 24))
        self.assertLess(observed.mae_24h, 0)
        self.assertGreater(observed.mfe_24h, 0)
        self.assertEqual(observed.recovery_minutes, 5)

    def test_runner_contains_no_returns_backtest_oos_or_trading_authorization(self) -> None:
        text = (ROOT / "scripts/m1h_run_is_paper_feasibility.py").read_text(encoding="utf-8").lower()
        for prohibited in ("create_order", "cancel_order", "place_order", "execution/live", "binance_api_key"):
            self.assertNotIn(prohibited, text)
        self.assertIn('"- formal strategy returns computed: no"', text)
        self.assertIn('"- backtest executed: no"', text)
        self.assertIn('"- oos opened: no"', text)
        self.assertIn('"- m2 authorized: no"', text)


if __name__ == "__main__":
    unittest.main()
