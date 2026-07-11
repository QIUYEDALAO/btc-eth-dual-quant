from __future__ import annotations

import json
import copy
import importlib.util
import unittest
from pathlib import Path

from btc_eth_dual_quant.audit.m1e_paper import detect_events, summarize


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads((ROOT / "config/m1e_is_paper_protocol.json").read_text())
HOUR = 3_600_000


def rows(symbol: str, count: int = 4380) -> list[dict]:
    output = []
    for index in range(count):
        price = 100.0
        high, low, close = 100.1, 99.9, 100.0
        if index == 4350:
            high, low, close = 102.5, 99.8, 102.0
        elif 4350 < index <= 4374:
            close = 102.0 + (index - 4350) * 0.08
            high, low = close + 0.1, close - 0.1
        output.append({
            "symbol": symbol, "timeframe": "1h", "open_time": 1593561600000 + index * HOUR,
            "close_time": 1593561600000 + (index + 1) * HOUR - 1,
            "open": str(price), "high": str(high), "low": str(low), "close": str(close),
            "volume": "1", "quote_volume": "100", "trade_count": "1",
            "taker_buy_base_volume": "0.5", "taker_buy_quote_volume": "50",
            "segment_id": 1, "bars_since_segment_start": index + 1,
        })
    return output


class M1EPaperTests(unittest.TestCase):
    def test_event_uses_only_prior_compression_and_completed_expansion(self) -> None:
        result = detect_events(rows("BTCUSDT"), PROTOCOL)
        self.assertEqual(len(result.events), 1)
        event = result.events[0]
        self.assertEqual(event.event_open_time, 1593561600000 + 4350 * HOUR)
        self.assertGreater(event.expansion_multiple, 2.0)
        self.assertGreater(event.mfe_24h, 0.0)

    def test_future_change_does_not_change_event_identity(self) -> None:
        original = rows("BTCUSDT")
        changed = rows("BTCUSDT")
        for index in range(4351, 4375):
            changed[index]["high"] = "120"
            changed[index]["close"] = "110"
        first = detect_events(original, PROTOCOL)
        second = detect_events(changed, PROTOCOL)
        self.assertEqual(first.events[0].event_open_time, second.events[0].event_open_time)
        self.assertNotEqual(first.events[0].mfe_24h, second.events[0].mfe_24h)

    def test_unrewarmed_segment_cannot_generate_event(self) -> None:
        data = rows("BTCUSDT")
        for row in data:
            row["bars_since_segment_start"] = min(row["bars_since_segment_start"], 100)
        result = detect_events(data, PROTOCOL)
        self.assertEqual(len(result.events), 0)

    def test_protocol_keeps_oos_and_strategy_outputs_disabled(self) -> None:
        self.assertFalse(PROTOCOL["scope"]["oos_opened"])
        self.assertFalse(PROTOCOL["scope"]["formal_strategy_return_permitted"])
        for key in ("fixed_rule_contract", "strategy_code", "freqtrade_backtesting", "oos_access", "m2"):
            self.assertFalse(PROTOCOL["authorization"][key])

    def test_summary_applies_frozen_gates_without_equity(self) -> None:
        btc = detect_events(rows("BTCUSDT"), PROTOCOL)
        eth = detect_events(rows("ETHUSDT"), PROTOCOL)
        summary = summarize([btc, eth], PROTOCOL)
        self.assertIn(summary["status"], {"pass", "failed_feasibility"})
        self.assertIn("projected_oos_events", summary)
        self.assertNotIn("equity", summary)

    def test_frozen_event_and_gate_protocol_cannot_change(self) -> None:
        spec = importlib.util.spec_from_file_location("m1e_paper_check", ROOT / "scripts/m1e_paper_check.py")
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        changed = copy.deepcopy(PROTOCOL)
        changed["paper_gates"]["median_24h_mfe_minimum"] = "0.0100"
        self.assertTrue(module.validate(changed))
        changed = copy.deepcopy(PROTOCOL)
        changed["diagnostic_event"]["compression_quantile"] = "0.30"
        self.assertTrue(module.validate(changed))


if __name__ == "__main__":
    unittest.main()
