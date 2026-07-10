from __future__ import annotations

import inspect
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from btc_eth_dual_quant.audit.feasibility import CandidateIdentity
from btc_eth_dual_quant.audit.sample_budget import (
    CalendarBudgetResult,
    SampleBudgetPolicy,
    evaluate_calendar_budget,
    extract_research_calendar_metadata,
)


ROOT = Path(__file__).resolve().parents[1]


def t1_manifest() -> dict:
    return {
        "schema_version": 1,
        "research_start": "2023-10-01",
        "requested_end": "2026-06-30T23:59:59.999000+00:00",
        "api_key_used": False,
        "private_data_used": False,
        "months": [{"large_runtime_detail": "ignored"}],
    }


def t2_manifest() -> dict:
    return {
        "schema_version": 1,
        "research_start": "2023-10-01",
        "research_end": "2026-06-30T23:59:59.999000+00:00",
        "api_key_used": False,
        "private_data_used": False,
        "research_blockers": [],
        "symbols": [{"runtime_detail": "ignored"}],
    }


def candidate(*, opened: bool = False) -> CandidateIdentity:
    return CandidateIdentity("M1D", "sealed", "a" * 64, "declared_unopened", opened)


class CalendarBudgetTests(unittest.TestCase):
    def result(self) -> CalendarBudgetResult:
        metadata = extract_research_calendar_metadata(t1_manifest(), t2_manifest())
        return evaluate_calendar_budget(metadata, candidate())

    def test_current_calendar_splits_to_1004_702_302(self) -> None:
        result = self.result()
        self.assertEqual((result.full_days, result.is_days, result.oos_days), (1004, 702, 302))
        self.assertEqual(result.oos_start_day, date(2025, 9, 2))
        self.assertEqual(result.research_start, date(2023, 10, 1))
        self.assertEqual(result.latest_complete_day, date(2026, 6, 30))

    def test_current_calendar_fails_fixed_540_day_gate(self) -> None:
        result = self.result()
        self.assertFalse(result.calendar_gate_passed)
        self.assertEqual(result.required_oos_days, 540)
        self.assertEqual(result.shortage_days, 238)
        self.assertEqual(result.status, "blocked_insufficient_oos_calendar")

    def test_1800_days_is_minimum_and_earliest_end_is_fixed(self) -> None:
        result = self.result()
        self.assertEqual(result.required_full_days, 1800)
        self.assertEqual(result.earliest_eligible_end_day, date(2028, 9, 3))

    def test_nonfixed_policy_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "frozen at 540"):
            SampleBudgetPolicy(required_oos_days=539)
        with self.assertRaisesRegex(ValueError, "frozen at 30"):
            SampleBudgetPolicy(oos_fraction=Decimal("0.29"))

    def test_opened_oos_and_nonempty_t2_blockers_are_rejected(self) -> None:
        metadata = extract_research_calendar_metadata(t1_manifest(), t2_manifest())
        with self.assertRaisesRegex(ValueError, "sealed OOS"):
            evaluate_calendar_budget(metadata, candidate(opened=True))
        blocked = t2_manifest()
        blocked["research_blockers"] = ["gap"]
        with self.assertRaisesRegex(ValueError, "research blockers"):
            evaluate_calendar_budget(extract_research_calendar_metadata(t1_manifest(), blocked), candidate())

    def test_manifest_mismatch_or_private_metadata_is_rejected(self) -> None:
        mismatched = t2_manifest()
        mismatched["research_end"] = "2026-06-29T23:59:59.999000+00:00"
        with self.assertRaisesRegex(ValueError, "latest complete"):
            extract_research_calendar_metadata(t1_manifest(), mismatched)
        private = t1_manifest()
        private["private_data_used"] = True
        with self.assertRaisesRegex(ValueError, "private-data"):
            extract_research_calendar_metadata(private, t2_manifest())
        incomplete = t1_manifest()
        incomplete["requested_end"] = "2026-06-30T12:00:00+00:00"
        matching_t2 = t2_manifest()
        matching_t2["research_end"] = incomplete["requested_end"]
        with self.assertRaisesRegex(ValueError, "final millisecond"):
            extract_research_calendar_metadata(incomplete, matching_t2)

    def test_canonical_hash_is_repeatable(self) -> None:
        self.assertEqual(self.result().canonical_sha256, self.result().canonical_sha256)

    def test_public_api_has_no_prices_returns_events_or_strategy_parameters(self) -> None:
        self.assertEqual(tuple(inspect.signature(evaluate_calendar_budget).parameters), ("metadata", "candidate"))
        source = inspect.getsource(evaluate_calendar_budget).casefold()
        for forbidden in ("ohlcv", "entry_price", "exit_price", "event_reference", "strategy_return"):
            self.assertNotIn(forbidden, source)

    def test_module_has_no_trading_or_strategy_implementation(self) -> None:
        source = (ROOT / "src/btc_eth_dual_quant/audit/sample_budget.py").read_text(encoding="utf-8")
        for forbidden in (
            "populate_entry",
            "populate_exit",
            "create_order",
            "cancel_order",
            "place_order",
            "execution/live",
            "freqtrade trade",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
