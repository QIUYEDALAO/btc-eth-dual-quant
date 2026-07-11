from __future__ import annotations

import json
import inspect
import unittest
from pathlib import Path

from btc_eth_dual_quant.audit.m1g_paper import detect_events, summarize


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads((ROOT / "config" / "m1g_is_paper_protocol.json").read_text(encoding="utf-8"))
HOUR_MS = 3_600_000


def rows(count: int = 200, event_index: int = 169) -> list[dict]:
    result = []
    price = 100.0
    for index in range(count):
        previous = price
        price = previous * (0.999 if index % 2 else 1.001)
        low = min(previous, price) * 0.999
        high = max(previous, price) * 1.001
        if index == event_index:
            price = previous * 0.97
            high = previous * 1.001
            low = price * 0.998
        result.append({
            "symbol": "BTCUSDT", "open_time": index * HOUR_MS, "open": previous,
            "high": high, "low": low, "close": price, "segment_id": 1,
            "bars_since_segment_start": index + 1,
        })
    return result


class M1GPaperTests(unittest.TestCase):
    def test_event_uses_prior_only_statistics_and_completed_bar(self) -> None:
        result = detect_events(rows(), PROTOCOL)
        self.assertEqual(result.raw_candidates, 1)
        self.assertEqual(len(result.events), 1)
        self.assertEqual(result.events[0].event_open_time, 169 * HOUR_MS)

    def test_future_path_change_does_not_change_event_identity(self) -> None:
        first = rows()
        second = rows()
        second[175]["high"] *= 1.2
        self.assertEqual(detect_events(first, PROTOCOL).events[0].event_open_time, detect_events(second, PROTOCOL).events[0].event_open_time)

    def test_unrewarmed_segment_rejects_event(self) -> None:
        data = rows()
        data[169]["bars_since_segment_start"] = 100
        self.assertEqual(detect_events(data, PROTOCOL).raw_candidates, 0)

    def test_summary_applies_frozen_gates_without_equity(self) -> None:
        result = detect_events(rows(), PROTOCOL)
        summary = summarize([result], PROTOCOL)
        self.assertEqual(summary["complete_events"], 1)
        self.assertNotIn("equity", summary)
        self.assertFalse(summary["gate_matrix"]["projected_full_events"])

    def test_module_has_no_fill_position_or_equity_engine(self) -> None:
        from btc_eth_dual_quant.audit import m1g_paper

        source = inspect.getsource(m1g_paper)
        for forbidden in ("create_order", "place_order", "cancel_order", "execution/live"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
