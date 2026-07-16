import ast
import copy
import unittest
from decimal import Decimal

from btc_eth_dual_quant.audit.liquid_universe_v4_independent import (
    audit_canonical_json,
    audit_content_hash,
    milliseconds_from_utc,
)
from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import scan_independence


class IndependentAuditorTests(unittest.TestCase):
    def test_canonicalization_is_order_independent_and_strict(self):
        left = {"b": Decimal("1.00"), "a": [2, 1], "generated_at": "x"}
        right = {"generated_at": "y", "a": [2, 1], "b": Decimal("1.00")}
        self.assertEqual(audit_content_hash(left), audit_content_hash(right))
        self.assertNotIn("generated_at", audit_canonical_json(left))
        with self.assertRaises(ValueError):
            audit_canonical_json({"value": float("nan")})

    def test_integer_utc_parser_never_uses_float_epoch(self):
        self.assertEqual(milliseconds_from_utc("2024-10-28T03:00:00Z"), 1730084400000)
        self.assertEqual(milliseconds_from_utc("2024-10-28T02:59:59.999000Z"), 1730084399999)

    def test_ast_scanner_rejects_production_import_and_calls(self):
        source = "from btc_eth_dual_quant.data.liquid_universe_pipeline_v4 import build_membership_rows\nbuild_membership_rows([])\n"
        findings = scan_independence(source)
        self.assertTrue(findings)
        self.assertEqual(scan_independence("import json\njson.dumps({})\n"), [])
