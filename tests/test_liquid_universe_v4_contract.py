import copy
import json
import unittest

from btc_eth_dual_quant.data.lifecycle_availability import LifecycleEventRegistry
from scripts.liquid_universe_v4_contract_check import validate
from tests.v4_lifecycle_fixtures import CONTRACT_PATH, POLICY_PATH, REGISTRY_PATH, ROOT


class V4ContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT_PATH.read_text())
        self.policy = json.loads(POLICY_PATH.read_text())
        self.registry = json.loads(REGISTRY_PATH.read_text())

    def test_contract_policy_registry_and_prior_authorities_are_hash_bound(self):
        result = validate(self.contract, self.policy, self.registry, root=ROOT)
        self.assertEqual(
            self.contract["bindings"]["adr0011_adr_sha256"],
            "5e05543cc7019fe7aaa6c90ebf78fb26adf084e33cb78aeccf6089202a1b94df",
        )
        self.assertEqual(result["contract_hash"], self.contract["canonical_hash"])
        self.assertEqual(result["policy_hash"], self.policy["canonical_hash"])
        self.assertEqual(result["registry_hash"], self.registry["canonical_hash"])
        self.assertFalse(any(result["downstream_authorizations"].values()))

    def test_mutated_contract_policy_or_reviewed_event_is_rejected(self):
        changed = copy.deepcopy(self.contract)
        changed["membership"]["target_size"] = 16
        with self.assertRaisesRegex(ValueError, "contract canonical hash"):
            validate(changed, self.policy, self.registry, root=ROOT)

        changed = copy.deepcopy(self.policy)
        changed["processing_order"] = list(reversed(changed["processing_order"]))
        with self.assertRaisesRegex(ValueError, "policy canonical hash"):
            validate(self.contract, changed, self.registry, root=ROOT)

        changed = copy.deepcopy(self.registry)
        changed["entries"][0]["affected_raw_rows"][0]["raw_row_sha256"] = "0" * 64
        changed["canonical_hash"] = LifecycleEventRegistry.compute_hash(changed)
        with self.assertRaisesRegex(ValueError, "reviewed lifecycle evidence"):
            validate(self.contract, self.policy, changed, root=ROOT)

    def test_production_runtime_has_no_symbol_or_date_special_case(self):
        paths = (
            ROOT / "src/btc_eth_dual_quant/data/lifecycle_availability.py",
            ROOT / "src/btc_eth_dual_quant/data/lifecycle_artifacts.py",
            ROOT / "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
        )
        forbidden = ('if symbol == "KLAYUSDT"', "2024-10-28", "2024-10-29", "2024-10-30", ".md")
        for path in paths:
            text = path.read_text()
            for token in forbidden:
                self.assertNotIn(token, text, f"{token} in {path}")


if __name__ == "__main__":
    unittest.main()
