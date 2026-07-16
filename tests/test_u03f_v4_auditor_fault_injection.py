import unittest

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import scan_float_timestamp_paths, validate_authorization


class FaultInjectionTests(unittest.TestCase):
    def test_float_timestamp_authority_path_is_high_finding(self):
        findings = scan_float_timestamp_paths("x = dt.timestamp() * 1_000\ny = datetime.fromtimestamp(ms / 1_000)")
        self.assertEqual(len(findings), 2)

    def test_any_authorization_true_fails(self):
        self.assertTrue(validate_authorization({"u04": True}))
        self.assertEqual(validate_authorization({"u04": False, "m2": False}), [])
