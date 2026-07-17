from __future__ import annotations

import copy
import unittest

from scripts.adr0015_adoption_check import (
    ADOPTED_ADR_PATH,
    DEPENDENCY_ORDER,
    EXPECTED_AUTHORIZATIONS,
    EXPECTED_REVIEW_BINDINGS,
    build_adoption_document,
    canonical_hash,
    content_identity,
    extract_semantic_body,
    verify_adoption_document,
)


class ADR0015AdoptionTests(unittest.TestCase):
    def test_exact_review_and_evidence_bindings_are_frozen(self) -> None:
        document = build_adoption_document(generated_utc="2026-07-17T04:00:00Z")
        self.assertEqual(document["review_bindings"], EXPECTED_REVIEW_BINDINGS)
        self.assertEqual(document["content"]["dependency_order"], DEPENDENCY_ORDER)
        self.assertEqual(verify_adoption_document(document), [])

    def test_authorization_matrix_is_exact_and_limited(self) -> None:
        self.assertEqual(
            {key for key, value in EXPECTED_AUTHORIZATIONS.items() if value},
            {
                "adr0015_adopted",
                "generic_policy_implementation",
                "fixture_validation",
                "fault_injection",
                "exact_head_implementation_review",
            },
        )
        for forbidden in (
            "fixed_range_public_requalification",
            "new_independent_audit_protocol",
            "new_independent_audit",
            "u04",
            "backtesting_or_oos",
            "api_or_trading",
            "execution_live",
            "m2",
        ):
            changed = build_adoption_document(generated_utc="2026-07-17T04:00:00Z")
            changed["content"]["authorization_matrix"][forbidden] = True
            self.assertIn("authorization matrix changed", verify_adoption_document(changed))

    def test_every_review_binding_rejects_tampering(self) -> None:
        for key, value in EXPECTED_REVIEW_BINDINGS.items():
            changed = build_adoption_document(generated_utc="2026-07-17T04:00:00Z")
            if isinstance(value, int):
                changed["review_bindings"][key] = value + 1
            elif value == "approve":
                changed["review_bindings"][key] = "reject"
            else:
                changed["review_bindings"][key] = "0" * 64
            self.assertIn(f"review binding changed: {key}", verify_adoption_document(changed))

    def test_semantic_body_excludes_adoption_metadata_and_heading_name(self) -> None:
        draft = "# Title\n\n- Status: Proposed\n\n## Proposed Decision\nPolicy  \n\n## Forbidden Shortcuts\n- no\n\n## Independent Policy Review Gate\nreview\n"
        adopted = "# Title\n\n- Status: Accepted\n\n## Decision\nPolicy\n\n## Forbidden Shortcuts\n- no\n\n## Independent Policy Review Result\nreview complete\n"
        self.assertEqual(extract_semantic_body(draft), extract_semantic_body(adopted))

    def test_semantic_body_change_is_hash_visible(self) -> None:
        original = "## Decision\nPolicy\n## Forbidden Shortcuts\n- no\n## Independent Policy Review Result\n"
        changed = original.replace("\nPolicy\n", "\nChanged\n")
        self.assertNotEqual(canonical_hash(extract_semantic_body(original)), canonical_hash(extract_semantic_body(changed)))

    def test_generation_time_does_not_change_content_identity(self) -> None:
        first = build_adoption_document(generated_utc="2026-07-17T04:00:00Z")
        second = build_adoption_document(generated_utc="2026-07-17T05:00:00Z")
        self.assertEqual(first["content_hash"], second["content_hash"])
        self.assertEqual(content_identity(first), content_identity(second))

    def test_document_hash_and_stage_effect_tampering_are_rejected(self) -> None:
        document = build_adoption_document(generated_utc="2026-07-17T04:00:00Z")
        changed = copy.deepcopy(document)
        changed["content_hash"] = "0" * 64
        self.assertIn("adoption content hash mismatch", verify_adoption_document(changed))
        changed = copy.deepcopy(document)
        changed["content"]["current_stage_effects"]["public_data_run_executed"] = True
        self.assertIn("adoption stage effects changed", verify_adoption_document(changed))

    def test_adopted_adr_path_is_fixed(self) -> None:
        self.assertEqual(
            ADOPTED_ADR_PATH.as_posix().split("/docs/", 1)[1],
            "decisions/ADR-0015-synchronized-official-invalid-interval-quarantine-policy.md",
        )


if __name__ == "__main__":
    unittest.main()
