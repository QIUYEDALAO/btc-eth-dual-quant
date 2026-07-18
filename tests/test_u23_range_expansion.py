from __future__ import annotations

import unittest

from btc_eth_dual_quant.data.u23_range_expansion import HISTORY_BARS, RangeStrengthDecision, evaluate_decision, evaluate_stream


def decision(order=range(15), *, weak_close=False, weak_range=False):
    symbols = tuple(f"S{index:02d}USDT" for index in order)
    by_symbol = {}
    paths = {}
    for index in range(15):
        history = []
        for offset in range(HISTORY_BARS):
            center = 100.0 + index + (offset % 3) * 0.01
            half = 0.45 + (offset % 7) * 0.025
            history.append((center, center + half, center - half, center + 0.02))
        current = (100.0, 100.8, 99.6, 100.2)
        if index == 14:
            current = (100.0, 102.0, 99.5, 101.0) if weak_range else ((100.0, 108.0, 99.5, 104.0) if weak_close else (100.0, 108.0, 99.5, 107.5))
        by_symbol[f"S{index:02d}USDT"] = tuple(history) + (current,)
        paths[f"S{index:02d}USDT"] = (0.001, 0.002, 0.004, 0.008, 0.012, 0.024)
    return RangeStrengthDecision(0, symbols, tuple(by_symbol[symbol] for symbol in symbols), tuple(paths[symbol] for symbol in symbols))


class U23CoreTests(unittest.TestCase):
    def test_positive_and_order_invariant(self):
        normal = evaluate_decision(decision())
        reverse = evaluate_decision(decision(reversed(range(15))))
        self.assertIsNotNone(normal)
        self.assertEqual(normal, reverse)
        self.assertEqual(normal["symbol"], "S14USDT")

    def test_range_and_close_fail_closed(self):
        self.assertIsNone(evaluate_decision(decision(weak_range=True)))
        self.assertIsNone(evaluate_decision(decision(weak_close=True)))

    def test_stream_order_and_cluster(self):
        first = decision()
        second = RangeStrengthDecision(14_400_000, first.symbols, first.completed_ohlc, first.path_displacements)
        result = evaluate_stream((first, second))
        self.assertEqual(result["candidate_events"], 2)
        self.assertEqual(result["independent_episodes"], 1)
        with self.assertRaises(ValueError):
            evaluate_stream((second, first))


if __name__ == "__main__":
    unittest.main()
