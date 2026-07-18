from __future__ import annotations

import unittest

from btc_eth_dual_quant.data.u22_dispersion_expansion import DispersionLeaderDecision, evaluate_decision, evaluate_stream


def decision(order=range(15), *, dominance=False, ratio=True):
    symbols = tuple(f"S{index:02d}USDT" for index in order)
    by_symbol = {}
    paths = {}
    for index in range(15):
        baseline = tuple((index - 7) * 0.0002 for _ in range(12))
        if index == 14:
            recent = (0.026,) + tuple(0.0002 for _ in range(11)) if dominance else tuple(0.0060 for _ in range(12))
        else:
            scale = 0.00025 if not ratio else 0.00075
            recent = tuple((index - 7) * scale - 0.0003 for _ in range(12))
        by_symbol[f"S{index:02d}USDT"] = baseline + recent
        paths[f"S{index:02d}USDT"] = (0.001, 0.002, 0.004, 0.008, 0.012, 0.024)
    return DispersionLeaderDecision(0, symbols, tuple(by_symbol[symbol] for symbol in symbols), tuple(paths[symbol] for symbol in symbols))


class U22CoreTests(unittest.TestCase):
    def test_positive_and_order_invariant(self):
        normal = evaluate_decision(decision())
        reverse = evaluate_decision(decision(reversed(range(15))))
        self.assertIsNotNone(normal)
        self.assertEqual(normal, reverse)
        self.assertEqual(normal["symbol"], "S14USDT")

    def test_dominance_and_dispersion_fail_closed(self):
        self.assertIsNone(evaluate_decision(decision(dominance=True)))
        self.assertIsNone(evaluate_decision(decision(ratio=False)))

    def test_stream_order_and_cluster(self):
        first = decision()
        second = DispersionLeaderDecision(3_600_000, first.symbols, first.completed_hourly_log_returns, first.path_displacements)
        result = evaluate_stream((first, second))
        self.assertEqual(result["candidate_events"], 2)
        self.assertEqual(result["independent_episodes"], 1)
        with self.assertRaises(ValueError):
            evaluate_stream((second, first))


if __name__ == "__main__":
    unittest.main()
