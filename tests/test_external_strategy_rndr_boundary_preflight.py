from __future__ import annotations

import copy
import hashlib
import io
import json
import unittest
import zipfile

from scripts.external_strategy_rndr_boundary_preflight import (
    ARCHIVE_URL,
    CHECKSUM_URL,
    EVIDENCE,
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_COMMAND_HASH,
    EXPECTED_EVIDENCE_HASH,
    EXPECTED_ROW_SHA256,
    FetchResult,
    ROOT,
    acquire,
    build_evidence,
    canonical_hash,
    validate,
)


def fixture_archive(*, duplicate: bool = False, bad_close: bool = False) -> bytes:
    target = [
        "1721616900000", "7.10000000", "7.20000000", "7.00000000", "7.15000000", "100.00000000",
        "1721617199998" if bad_close else "1721617199999", "715.00000000", "42", "50.00000000", "357.50000000", "0",
    ]
    rows = []
    for offset in range(-5, 6):
        if offset == 0:
            rows.append(",".join(target))
            continue
        open_ms = 1721616900000 + offset * 300000
        rows.append(f"{open_ms},7,7,7,7,1,{open_ms + 299999},7,1,1,7,0")
    if duplicate:
        rows.append(",".join(target))
    handle = io.BytesIO()
    with zipfile.ZipFile(handle, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("RNDRUSDT-5m-2024-07-22.csv", "\n".join(rows) + "\n")
    return handle.getvalue()


def responses(archive_body: bytes) -> tuple[FetchResult, FetchResult]:
    digest = hashlib.sha256(archive_body).hexdigest()
    archive = FetchResult(ARCHIVE_URL, ARCHIVE_URL, 200, archive_body, {"content-length": str(len(archive_body)), "content-type": "application/zip"})
    checksum = FetchResult(CHECKSUM_URL, CHECKSUM_URL, 200, f"{digest}  RNDRUSDT-5m-2024-07-22.zip\n".encode(), {})
    return archive, checksum


class ExternalStrategyRndrBoundaryPreflightTests(unittest.TestCase):
    def frozen(self) -> dict:
        return json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_frozen_evidence_is_exact_and_fail_closed(self) -> None:
        self.assertIsNotNone(EXPECTED_EVIDENCE_HASH)
        self.assertIsNotNone(EXPECTED_COMMAND_HASH)
        self.assertIsNotNone(EXPECTED_ARCHIVE_SHA256)
        self.assertIsNotNone(EXPECTED_ROW_SHA256)
        self.assertEqual(validate(ROOT, self.frozen()), [])

    def test_three_real_orders_and_generation_time_independence(self) -> None:
        archive, checksum = responses(fixture_archive())
        first = build_evidence(
            archive, checksum, generated_utc="2026-01-01T00:00:00Z", acquired_at_utc="2026-01-01T00:00:00Z"
        )
        second = build_evidence(
            archive, checksum, generated_utc="2026-02-01T00:00:00Z", acquired_at_utc="2026-01-01T00:00:00Z"
        )
        self.assertEqual(first["content_hash"], second["content_hash"])
        self.assertEqual(len(set(first["construction_result_hashes"].values())), 1)
        self.assertEqual(len(set(first["construction_trace_hashes"].values())), 3)
        self.assertFalse(first["completed_authority_nb01_satisfied"])

    def test_duplicate_and_bad_close_fail(self) -> None:
        for body in (fixture_archive(duplicate=True), fixture_archive(bad_close=True)):
            archive, checksum = responses(body)
            with self.assertRaises(ValueError):
                build_evidence(archive, checksum)

    def test_acquisition_requests_only_archive_and_checksum(self) -> None:
        archive, checksum = responses(fixture_archive())
        calls: list[str] = []

        def fetch(url: str) -> FetchResult:
            calls.append(url)
            return archive if url == ARCHIVE_URL else checksum

        acquire(fetch)
        self.assertEqual(calls, [ARCHIVE_URL, CHECKSUM_URL])

    def test_tamper_with_recomputed_hash_still_fails(self) -> None:
        mutations = (
            lambda value: value["source"].__setitem__("archive_sha256", "0" * 64),
            lambda value: value["exact_row"].__setitem__("raw_line_sha256", "0" * 64),
            lambda value: value["isolation"].__setitem__("other_91_archives_requested", 1),
            lambda value: value["next_stage"].__setitem__("original_is_authorized", True),
            lambda value: value["permissions"].__setitem__("oos", True),
        )
        for mutation in mutations:
            evidence = copy.deepcopy(self.frozen())
            mutation(evidence)
            evidence["content_hash"] = canonical_hash(evidence)
            self.assertTrue(validate(ROOT, evidence))

if __name__ == "__main__":
    unittest.main()
