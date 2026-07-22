from __future__ import annotations

import copy
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.external_strategy_boundary_authority_build import (
    EVIDENCE,
    EXPECTED_COMMAND_HASH,
    EXPECTED_EVIDENCE_HASH,
    NEW_RNDR,
    OLD_RNDR,
    ROOT,
    canonical_hash,
    inspect_archive,
    revised_boundaries,
    validate,
)


def fixture_zip(symbol: str, day: str, open_ms: int, *, duplicate: bool = False, close_delta: int = 299999) -> bytes:
    row = f"{open_ms},2,3,1,2,10,{open_ms + close_delta},20,4,5,10,0"
    rows = [row, f"{open_ms + 300000},2,3,1,2,10,{open_ms + 599999},20,4,5,10,0"]
    if duplicate:
        rows.append(row)
    handle = io.BytesIO()
    with zipfile.ZipFile(handle, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{symbol}-5m-{day}.csv", "\n".join(rows) + "\n")
    return handle.getvalue()


class CompletedBoundaryAuthorityTests(unittest.TestCase):
    def evidence(self) -> dict:
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_frozen_authority_is_exact(self) -> None:
        self.assertIsNotNone(EXPECTED_EVIDENCE_HASH)
        self.assertIsNotNone(EXPECTED_COMMAND_HASH)
        self.assertEqual(validate(ROOT, self.evidence()), [])

    def test_revised_set_is_exact_one_for_one(self) -> None:
        boundaries = revised_boundaries(ROOT)
        identities = {(row["symbol"], row["membership_end_exclusive"]) for row in boundaries}
        self.assertEqual(len(boundaries), 92)
        self.assertNotIn(OLD_RNDR, identities)
        self.assertIn(NEW_RNDR, identities)

    def test_exact_row_duplicate_and_timestamp_fail_closed(self) -> None:
        boundary = {"symbol": "TESTUSDT", "membership_end_exclusive": "2024-01-01T00:00:00Z"}
        open_ms = 1704067200000
        parsed = inspect_archive(fixture_zip("TESTUSDT", "2024-01-01", open_ms), boundary)
        self.assertEqual(parsed["row"]["open_time_ms"], open_ms)
        for body in (
            fixture_zip("TESTUSDT", "2024-01-01", open_ms, duplicate=True),
            fixture_zip("TESTUSDT", "2024-01-01", open_ms, close_delta=300000),
            fixture_zip("WRONGUSDT", "2024-01-01", open_ms),
        ):
            with self.assertRaises(ValueError):
                inspect_archive(body, boundary)

        sealed_oos = {"symbol": "TESTUSDT", "membership_end_exclusive": "2024-09-11T00:00:00Z"}
        with self.assertRaises(ValueError):
            inspect_archive(fixture_zip("TESTUSDT", "2024-09-11", 1726012800000), sealed_oos)

    def test_tamper_with_recomputed_hash_still_fails(self) -> None:
        mutations = (
            lambda value: value["records"][0].__setitem__("archive_sha256", "0" * 64),
            lambda value: value["records"][0]["row"].__setitem__("raw_line_sha256", "0" * 64),
            lambda value: value["source_accounting"].__setitem__("new_archives_downloaded", 90),
            lambda value: value.__setitem__("completed_authority_nb01_satisfied", False),
            lambda value: value["runtime_consumption_contract"].__setitem__("inactive_interval_state_carry", True),
            lambda value: value["permissions"].__setitem__("original_is", True),
            lambda value: value["records"][0].__setitem__("source_relative_path", "elsewhere.zip"),
            lambda value: value["records"][0]["policy_status"].__setitem__("eligibility_status", "unknown"),
            lambda value: value["construction_passes"]["reverse"]["trace"].reverse(),
            lambda value: value.__setitem__("status", "complete"),
            lambda value: value["permissions"].pop("m2"),
        )
        for mutation in mutations:
            evidence = copy.deepcopy(self.evidence())
            mutation(evidence)
            evidence["content_hash"] = canonical_hash(evidence)
            self.assertTrue(validate(ROOT, evidence))

    def test_generation_time_is_not_identity(self) -> None:
        first = copy.deepcopy(self.evidence())
        second = copy.deepcopy(first)
        first["generated_utc"] = "2026-01-01T00:00:00Z"
        second["generated_utc"] = "2026-02-01T00:00:00Z"
        self.assertEqual(canonical_hash(first), canonical_hash(second))

    def test_raw_archives_are_not_repository_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertFalse((Path(temporary) / "storage/raw").exists())
        tracked = __import__("subprocess").run(
            ["git", "ls-files", "storage/raw/external_strategy_boundary_authority"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(tracked, "")


if __name__ == "__main__":
    unittest.main()
