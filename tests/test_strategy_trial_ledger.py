from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "strategy_trial_ledger_check", ROOT / "scripts" / "strategy_trial_ledger_check.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def valid_ledger() -> dict:
    hypothesis = "A fixed hypothesis that has not opened OOS."
    return {
        "version": 1,
        "hash_algorithm": "sha256",
        "rules": {
            "oos_opening_increments_trial_count": True,
            "post_freeze_rule_change_creates_new_candidate": True,
            "failed_or_rejected_candidates_are_append_only": True,
        },
        "candidates": [
            {
                "id": "CANDIDATE-A",
                "status": "declared_unopened",
                "hypothesis": hypothesis,
                "sha256": hashlib.sha256(hypothesis.encode("utf-8")).hexdigest(),
                "oos_opened": False,
            }
        ],
    }


class StrategyTrialLedgerCheckTests(unittest.TestCase):
    def validate(self, data: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.yaml"
            path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            return MODULE.validate_ledger(path)

    def test_valid_ledger_passes(self) -> None:
        self.assertEqual(self.validate(valid_ledger()), [])

    def test_stale_hash_fails_after_hypothesis_change(self) -> None:
        data = valid_ledger()
        data["candidates"][0]["hypothesis"] += " Changed after freeze."
        failures = self.validate(data)
        self.assertTrue(any("sha256 mismatch" in failure for failure in failures))

    def test_duplicate_candidate_id_fails(self) -> None:
        data = valid_ledger()
        data["candidates"].append(dict(data["candidates"][0]))
        failures = self.validate(data)
        self.assertIn("duplicate candidate id: CANDIDATE-A", failures)

    def test_missing_required_rule_and_field_fail(self) -> None:
        data = valid_ledger()
        del data["rules"]["failed_or_rejected_candidates_are_append_only"]
        del data["candidates"][0]["status"]
        failures = self.validate(data)
        self.assertTrue(any("required rule must be true" in failure for failure in failures))
        self.assertTrue(any("missing fields: status" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
