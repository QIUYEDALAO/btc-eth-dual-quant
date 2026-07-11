import copy, json, unittest
from pathlib import Path
from scripts.liquid_universe_contract_check import canonical_hash, validate

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / "config/liquid_spot_universe_contract.json").read_text())

class LiquidUniverseContractTests(unittest.TestCase):
    def test_repository_contract_passes(self): self.assertEqual(validate(BASE), [])
    def test_membership_values_are_frozen(self):
        for key, value in (("target_size", 20), ("ranking_window_complete_days", 30), ("minimum_complete_history_days", 180)):
            changed = copy.deepcopy(BASE); changed["membership"][key] = value; changed["canonical_hash"] = canonical_hash(changed)
            self.assertTrue(validate(changed))
    def test_current_market_and_downstream_work_remain_disabled(self):
        changed = copy.deepcopy(BASE); changed["authorizations"]["returns"] = True; changed["canonical_hash"] = canonical_hash(changed)
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(BASE); changed["data_authority"]["current_exchange_info_is_historical_authority"] = True; changed["canonical_hash"] = canonical_hash(changed)
        self.assertTrue(validate(changed))
    def test_hash_is_deterministic(self): self.assertEqual(canonical_hash(BASE), canonical_hash(copy.deepcopy(BASE)))
    def test_gap_policy_forbids_manual_deletion_and_synthetic_fill(self):
        for key in ("manual_symbol_deletion_allowed", "synthetic_fill_or_interpolation_allowed"):
            changed=copy.deepcopy(BASE); changed["gap_handling_policy"][key]=True; changed["canonical_hash"]=canonical_hash(changed)
            self.assertTrue(validate(changed))

if __name__ == "__main__": unittest.main()
