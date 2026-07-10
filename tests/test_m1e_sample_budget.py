from __future__ import annotations

import inspect
import tempfile
import unittest
from datetime import date
from pathlib import Path

from btc_eth_dual_quant.audit.feasibility import CandidateIdentity, validate_candidate_identity
from btc_eth_dual_quant.audit.sample_budget import (
    SampleBudgetPolicy,
    evaluate_calendar_budget,
    extract_m1e_requalification_metadata,
)

ROOT = Path(__file__).resolve().parents[1]
HYPOTHESIS = (
    "M1E-1H-TREND-BREAKOUT: BTC/USDT and ETH/USDT Binance spot, long/cash only; "
    "completed UTC 1h candles define a trend-breakout candidate family distinct from M1A; "
    "entries may execute no earlier than the next available 5m open after the completed signal "
    "candle; completed 4h candles may be used only as a regime filter; no shorting or leverage."
)
DIGEST = "3668032467e2f46edff7f0ab27d358d0b918889518bfaf97276699cbc783ed15"


def manifest() -> dict:
    return {
        "schema_version": 2,
        "status": "pass",
        "research_start": "2020-07-01",
        "range_end": "2026-06-30T23:59:59.999000+00:00",
        "unresolved_5m_conflicts": 0,
        "incomplete_child_buckets": 0,
        "canonical_traceable": True,
        "freqtrade_runtime": {"status": "pass", "ignored_entries": ["no runtime dependency"]},
        "api_key_used": False,
        "private_data_used": False,
        "candidate_evaluated": False,
        "oos_accessed": False,
        "strategy_returns_computed": False,
        "datasets": [{"ignored_runtime_detail": "not inspected"}],
    }


def candidate(*, opened: bool = False, status: str = "declared_unopened") -> CandidateIdentity:
    return CandidateIdentity("M1E-1H-TREND-BREAKOUT", HYPOTHESIS, DIGEST, status, opened)


class M1ESampleBudgetTests(unittest.TestCase):
    def result(self):
        return evaluate_calendar_budget(extract_m1e_requalification_metadata(manifest()), candidate())

    def test_fixed_calendar_passes_2191_1533_658(self) -> None:
        result = self.result()
        self.assertEqual((result.full_days, result.is_days, result.oos_days), (2191, 1533, 658))
        self.assertEqual(result.oos_start_day, date(2024, 9, 11))
        self.assertEqual(result.earliest_eligible_end_day, date(2025, 6, 4))
        self.assertEqual(result.shortage_days, 0)
        self.assertTrue(result.calendar_gate_passed)

    def test_manifest_gate_rejects_every_material_failure(self) -> None:
        cases = (
            ("status", "blocked"), ("unresolved_5m_conflicts", 1),
            ("incomplete_child_buckets", 1), ("canonical_traceable", False),
            ("api_key_used", True), ("private_data_used", True),
            ("candidate_evaluated", True), ("oos_accessed", True),
            ("strategy_returns_computed", True),
        )
        for key, value in cases:
            changed = manifest(); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                extract_m1e_requalification_metadata(changed)
        changed = manifest(); changed["freqtrade_runtime"]["status"] = "fail"
        with self.assertRaisesRegex(ValueError, "Freqtrade"):
            extract_m1e_requalification_metadata(changed)

    def test_policy_and_trial_identity_remain_frozen_and_sealed(self) -> None:
        with self.assertRaises(ValueError):
            SampleBudgetPolicy(required_oos_days=539)
        metadata = extract_m1e_requalification_metadata(manifest())
        with self.assertRaisesRegex(ValueError, "sealed OOS"):
            evaluate_calendar_budget(metadata, candidate(opened=True))
        with self.assertRaisesRegex(ValueError, "declared_unopened"):
            evaluate_calendar_budget(metadata, candidate(status="under_review"))

    def test_duplicate_or_changed_ledger_identity_is_rejected(self) -> None:
        entry = (
            "version: 1\nhash_algorithm: sha256\ncandidates:\n"
            f"  - id: M1E-1H-TREND-BREAKOUT\n    status: declared_unopened\n    hypothesis: '{HYPOTHESIS}'\n"
            f"    sha256: {DIGEST}\n    oos_opened: false\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.yaml"
            path.write_text(entry, encoding="utf-8")
            validate_candidate_identity(path, candidate_id="M1E-1H-TREND-BREAKOUT", expected_hypothesis=HYPOTHESIS, expected_sha256=DIGEST)
            path.write_text(entry + entry.split("candidates:\n", 1)[1], encoding="utf-8")
            with self.assertRaises(ValueError):
                validate_candidate_identity(path, candidate_id="M1E-1H-TREND-BREAKOUT", expected_hypothesis=HYPOTHESIS, expected_sha256=DIGEST)

    def test_public_api_and_script_have_no_market_or_trading_inputs(self) -> None:
        self.assertEqual(tuple(inspect.signature(evaluate_calendar_budget).parameters), ("metadata", "candidate"))
        self.assertEqual(tuple(inspect.signature(extract_m1e_requalification_metadata).parameters), ("manifest",))
        source = (ROOT / "scripts/m1e_sample_budget_precheck.py").read_text(encoding="utf-8").casefold()
        for forbidden in ("entry_price", "exit_price", "create_order", "cancel_order", "freqtrade trade"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
