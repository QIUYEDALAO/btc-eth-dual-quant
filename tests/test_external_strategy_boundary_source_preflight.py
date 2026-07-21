from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.external_strategy_boundary_source_preflight import ROOT, canonical_hash, fixed_transitions, validate


EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/source_preflight.json"


class ExternalStrategyBoundarySourcePreflightTests(unittest.TestCase):
    def evidence(self) -> dict:
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_fixed_set_and_truthful_terminal_evidence(self) -> None:
        evidence = self.evidence()
        self.assertEqual(validate(ROOT, evidence), [])
        _, transitions = fixed_transitions(ROOT)
        self.assertEqual(len(transitions), 92)
        self.assertEqual(evidence["available_source_count"], 91)
        self.assertEqual(evidence["missing_source_count"], 1)
        self.assertEqual(evidence["missing_sources"][0]["symbol"], "RNDRUSDT")
        self.assertEqual(evidence["missing_sources"][0]["http_status"], 404)

    def test_tamper_and_permission_escalation_fail(self) -> None:
        for mutate in (
            lambda value: value.__setitem__("missing_source_count", 0),
            lambda value: value["source_checks"][0].__setitem__("source_url", "https://example.invalid/a.zip"),
            lambda value: value.__setitem__("original_is_authorized", True),
            lambda value: value.__setitem__("oos_rows_decoded", 1),
        ):
            evidence = copy.deepcopy(self.evidence())
            mutate(evidence)
            evidence["content_hash"] = canonical_hash(evidence)
            self.assertTrue(validate(ROOT, evidence))

    def test_authority_and_qualification_hash_tamper_fail(self) -> None:
        for key in ("authorization_hash", "qualification_hash"):
            evidence = copy.deepcopy(self.evidence())
            evidence[key] = "0" * 64
            evidence["content_hash"] = canonical_hash(evidence)
            self.assertTrue(validate(ROOT, evidence))

    def test_three_orders_and_zero_access_counters(self) -> None:
        evidence = self.evidence()
        self.assertEqual(len(set(evidence["construction_order_hashes"].values())), 1)
        for key in (
            "archives_downloaded",
            "archive_bytes_downloaded",
            "market_rows_decoded",
            "strategy_result_rows_read",
            "is_trials_materialized",
            "selection_trial_count",
            "oos_rows_decoded",
        ):
            self.assertEqual(evidence[key], 0)

    def test_materializer_requires_explicit_qualified_membership(self) -> None:
        source = (ROOT / "scripts/external_strategy_is_data_materialize.py").read_text(encoding="utf-8")
        self.assertIn('row.get("eligibility_status") == "qualified"', source)


if __name__ == "__main__":
    unittest.main()
