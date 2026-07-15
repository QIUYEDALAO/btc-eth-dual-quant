import copy
import unittest

from scripts.adr0014_adoption_check import (
    ADOPTED_ADR_PATH,
    EXPECTED_AUTHORIZATIONS,
    EXPECTED_REVIEW_BINDINGS,
    build_adoption_document,
    canonical_hash,
    content_identity,
    extract_semantic_body,
    verify_adoption_document,
    verify_repository,
)


class ADR0014AdoptionTests(unittest.TestCase):
    def test_exact_review_evidence_is_bound(self):
        document = build_adoption_document(generated_utc="2026-07-16T00:00:00Z")
        self.assertEqual(document["review_bindings"], EXPECTED_REVIEW_BINDINGS)
        self.assertEqual(document["content"]["authorization_matrix"], EXPECTED_AUTHORIZATIONS)
        self.assertEqual(verify_adoption_document(document), [])

    def test_authorization_matrix_is_exact_and_limited(self):
        self.assertEqual(
            {key for key, value in EXPECTED_AUTHORIZATIONS.items() if value},
            {
                "lifecycle_policy_adopted",
                "v4_contract_implementation",
                "v4_lifecycle_policy_implementation",
                "v4_lifecycle_event_registry_implementation",
                "fixture_validation",
                "fault_injection",
                "fixed_range_v4_public_requalification",
            },
        )
        changed = build_adoption_document(generated_utc="2026-07-16T00:00:00Z")
        changed["content"]["authorization_matrix"]["u03f_execution"] = True
        self.assertIn("authorization matrix changed", verify_adoption_document(changed))

    def test_review_binding_tampering_is_rejected(self):
        for key in (
            "reviewed_pr_head",
            "reviewed_pr_base",
            "reviewed_adr_sha256",
            "policy_model_hash",
            "fault_matrix_hash",
            "mc_conformance_hash",
            "prior_review_content_hash",
            "conformance_review_content_hash",
            "klay_adjudication_evidence_hash",
        ):
            changed = build_adoption_document(generated_utc="2026-07-16T00:00:00Z")
            changed["review_bindings"][key] = "0" * 64
            self.assertIn(f"review binding changed: {key}", verify_adoption_document(changed))

    def test_semantic_body_excludes_adoption_metadata(self):
        draft = """# Title\n\n- Status: Proposed\n\n## MC-01: One\nBody  \n\n## Forbidden Shortcuts\n- no\n\n## Draft Authorization Matrix\n- false\n"""
        adopted = """# Title\n\n- Status: Accepted\n\n## Adoption Scope\nmetadata\n\n## MC-01: One\nBody\n\n## Forbidden Shortcuts\n- no\n\n## Adoption Authorization Matrix\n- true\n"""
        self.assertEqual(extract_semantic_body(draft), extract_semantic_body(adopted))

    def test_semantic_body_change_is_hash_visible(self):
        original = "## MC-01: One\nBody\n## Forbidden Shortcuts\n- no\n## Draft Authorization Matrix\n"
        changed = original.replace("Body", "Changed")
        self.assertNotEqual(canonical_hash(extract_semantic_body(original)), canonical_hash(extract_semantic_body(changed)))

    def test_generation_time_does_not_change_content_identity(self):
        first = build_adoption_document(generated_utc="2026-07-16T00:00:00Z")
        second = build_adoption_document(generated_utc="2026-07-16T01:00:00Z")
        self.assertEqual(first["content_hash"], second["content_hash"])
        self.assertEqual(content_identity(first), content_identity(second))

    def test_document_hash_tampering_is_rejected(self):
        document = build_adoption_document(generated_utc="2026-07-16T00:00:00Z")
        changed = copy.deepcopy(document)
        changed["content_hash"] = "0" * 64
        self.assertIn("adoption content hash mismatch", verify_adoption_document(changed))

    def test_adopted_adr_path_is_fixed(self):
        self.assertEqual(
            ADOPTED_ADR_PATH.as_posix().split("/docs/", 1)[1],
            "decisions/ADR-0014-official-lifecycle-boundary-placeholder-policy.md",
        )

    def test_later_stages_can_recheck_evidence_without_reopening_adoption_scope(self):
        self.assertEqual(verify_repository(check_stage_scope=False), [])


if __name__ == "__main__":
    unittest.main()
