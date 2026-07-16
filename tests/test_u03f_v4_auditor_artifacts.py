import unittest

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import compare_manifest, make_manifest


class ArtifactTests(unittest.TestCase):
    def test_wrapper_content_and_order_are_compared(self):
        manifest = make_manifest("x", [{"a": 1}, {"a": 2}])
        self.assertEqual(compare_manifest(manifest, manifest)["mismatch_count"], 0)
        changed = make_manifest("x", [{"a": 2}, {"a": 1}])
        result = compare_manifest(manifest, changed)
        self.assertGreater(result["mismatch_count"], 0)
        self.assertIsNotNone(result["first_mismatch"])
