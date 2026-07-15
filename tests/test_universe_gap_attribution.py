from datetime import datetime, timedelta, timezone
import unittest

from btc_eth_dual_quant.data.universe_gap_attribution import GapRecord, classify_missing_slots, gate, quarantine_manifest

POLICY = {"synchronous_outage_minimum_symbols": 2, "synchronous_outage_minimum_fraction": 0.8}
T = datetime(2024, 1, 1, tzinfo=timezone.utc)


def classify(*, missing_by_slot, verified, confirmed=None, member_count=5):
    return classify_missing_slots(
        symbol="AUSDT",
        month="2024-01",
        missing={T},
        missing_by_slot=missing_by_slot,
        member_count=member_count,
        evidence_source="official ZIP",
        policy=POLICY,
        verified_symbols=verified,
        confirmed_symbol_months=confirmed or set(),
    )


class GapAttributionTests(unittest.TestCase):
    def test_unexplained_gap_cannot_pass(self):
        records = classify(missing_by_slot={T: {"AUSDT"}}, verified={"AUSDT"})
        self.assertEqual(records[0].classification, "unresolved")
        self.assertEqual(gate(records, [])[0], "blocked_unresolved")

    def test_global_outage_requires_every_archive_verified(self):
        missing = {T: {"AUSDT", "BUSDT", "CUSDT", "DUSDT"}}
        unresolved = classify(missing_by_slot=missing, verified={"AUSDT", "BUSDT", "CUSDT", "DUSDT"})
        self.assertEqual(unresolved[0].classification, "unresolved")
        global_event = classify(missing_by_slot=missing, verified={"AUSDT", "BUSDT", "CUSDT", "DUSDT", "EUSDT"})
        self.assertEqual(global_event[0].classification, "binance_global_event")
        self.assertEqual(gate(global_event, [])[0], "pass_with_quarantine")

    def test_confirmed_symbol_gap_isolates_entire_month(self):
        records = classify(missing_by_slot={T: {"AUSDT"}}, verified={"AUSDT"}, confirmed={("AUSDT", "2024-01")})
        self.assertEqual(records[0].qualification_decision, "quarantine_entire_symbol_month_without_replacement")

    def test_processing_and_empty_universe_block(self):
        self.assertEqual(gate([], ["parser"])[0], "blocked_processing_error")
        self.assertEqual(gate([], [], universe_months=0)[0], "blocked_empty_universe")

    def test_class_change_splits_contiguous_interval(self):
        second = T + timedelta(minutes=5)
        records = classify_missing_slots(
            symbol="AUSDT",
            month="2024-01",
            missing={T, second},
            missing_by_slot={T: {"AUSDT", "BUSDT"}, second: {"AUSDT"}},
            member_count=2,
            evidence_source="zip",
            policy=POLICY,
            verified_symbols={"AUSDT", "BUSDT"},
            confirmed_symbol_months={("AUSDT", "2024-01")},
        )
        self.assertEqual(len(records), 2)

    def test_global_scope_applies_to_all_members_and_symbol_scope_to_month(self):
        global_record = GapRecord("AUSDT", "2024-01", T, 1, 5, "binance_global_event", "verified", "quarantine_global_window_all_members")
        symbol_record = GapRecord("AUSDT", "2024-01", T + timedelta(hours=1), 1, 5, "symbol_specific_confirmed_archive_gap", "verified", "quarantine_entire_symbol_month_without_replacement")
        manifest = quarantine_manifest([global_record, symbol_record], {"2024-01": ["AUSDT", "BUSDT"]}, contract_hash="c", registry_hash="r")
        global_scope = next(scope for scope in manifest["scopes"] if scope["scope"] == "global_window")
        self.assertEqual(global_scope["affected_symbols"], ["AUSDT", "BUSDT"])
        self.assertEqual(next(scope for scope in manifest["scopes"] if scope["scope"] == "symbol_month")["symbol"], "AUSDT")


if __name__ == "__main__":
    unittest.main()
