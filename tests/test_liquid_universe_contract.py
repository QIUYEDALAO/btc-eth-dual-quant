import copy
from datetime import date
import json
from pathlib import Path
import unittest

from btc_eth_dual_quant.data.liquid_universe import exclusion_record, validate_registry
from scripts.liquid_universe_contract_check import canonical_hash, validate

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text())
REGISTRY = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text())


class LiquidUniverseContractTests(unittest.TestCase):
    def test_repository_contract_and_registry_pass(self):
        self.assertEqual(validate(BASE, REGISTRY), [])
        self.assertEqual(validate_registry(REGISTRY), [])

    def test_membership_values_are_frozen_even_with_recomputed_hash(self):
        for key, value in (("target_size", 20), ("ranking_window_complete_days", 30), ("minimum_complete_history_days", 180)):
            changed = copy.deepcopy(BASE)
            changed["membership"][key] = value
            changed["canonical_hash"] = canonical_hash(changed)
            self.assertTrue(validate(changed, REGISTRY))

    def test_downstream_authorization_remains_disabled(self):
        for key in ("hypothesis_preregistration", "strategy_selection", "event_scan", "returns", "oos_access", "freqtrade_backtesting", "m2", "api_or_trading"):
            changed = copy.deepcopy(BASE)
            changed["authorizations"][key] = True
            changed["canonical_hash"] = canonical_hash(changed)
            self.assertTrue(validate(changed, REGISTRY))

    def test_asset_categories_and_suffix_false_positive(self):
        effective = date(2026, 6, 1)
        for symbol in ("USD1USDT", "USDCUSDT", "FDUSDUSDT", "WBTCUSDT", "WBETHUSDT", "BTCUPUSDT"):
            self.assertIsNotNone(exclusion_record(symbol, effective, BASE, REGISTRY), symbol)
        self.assertEqual(exclusion_record("PAXGUSDT", effective, BASE, REGISTRY)["category"], "commodity_backed_or_external_reference_asset")
        self.assertIsNone(exclusion_record("JUPUSDT", effective, BASE, REGISTRY))
        self.assertIsNone(exclusion_record("MAKEUPUSDT", effective, BASE, REGISTRY))

    def test_registry_effective_boundary(self):
        self.assertIsNone(exclusion_record("USD1USDT", date(2025, 5, 21), BASE, REGISTRY))
        self.assertIsNotNone(exclusion_record("USD1USDT", date(2025, 5, 22), BASE, REGISTRY))

    def test_unknown_category_and_overlap_fail_closed(self):
        changed = copy.deepcopy(REGISTRY)
        changed["records"][0]["category"] = "unknown"
        self.assertTrue(validate_registry(changed))
        changed = copy.deepcopy(REGISTRY)
        duplicate = copy.deepcopy(changed["records"][0])
        duplicate["effective_from"] = "2025-01-01"
        changed["records"].append(duplicate)
        self.assertTrue(validate_registry(changed))


if __name__ == "__main__":
    unittest.main()
