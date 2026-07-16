from __future__ import annotations

import hashlib
import importlib.util
import copy
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "u03f_v4_invalid_interval_adjudication",
    ROOT / "scripts/liquid_universe_v4_invalid_interval_adjudication.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

CHECK_SPEC = importlib.util.spec_from_file_location(
    "u03f_v4_invalid_interval_adjudication_check",
    ROOT / "scripts/liquid_universe_v4_invalid_interval_adjudication_check.py",
)
CHECK = importlib.util.module_from_spec(CHECK_SPEC)
assert CHECK_SPEC.loader is not None
CHECK_SPEC.loader.exec_module(CHECK)


def kline(open_time: int, close_time: int) -> str:
    return ",".join(
        (
            str(open_time),
            "1.0",
            "2.0",
            "0.5",
            "1.5",
            "10.0",
            str(close_time),
            "15.0",
            "1",
            "5.0",
            "7.5",
            "0",
        )
    )


class InvalidIntervalTests(unittest.TestCase):
    def test_frozen_evidence_and_exact_report_pass_checker(self) -> None:
        documents = CHECK.load_documents()
        self.assertEqual(CHECK.validate_wrappers(documents), [])
        self.assertEqual(CHECK.validate_bindings(documents), [])
        self.assertEqual(CHECK.validate_diagnostic(documents), [])
        self.assertEqual(CHECK.validate_run_and_report(documents), [])

    def test_policy_or_authorization_tampering_fails_checker(self) -> None:
        documents = CHECK.load_documents()
        changed = copy.deepcopy(documents)
        changed["policy_gap_assessment"]["content"][
            "direct_existing_gap_policy_adoption_allowed"
        ] = True
        self.assertTrue(CHECK.validate_diagnostic(changed))
        changed = copy.deepcopy(documents)
        changed["authorization_matrix"]["content"]["u04"] = True
        self.assertTrue(CHECK.validate_diagnostic(changed))

    def test_frozen_inputs_and_authorization_matrix(self) -> None:
        _, freeze, membership, summary = MODULE.validate_inputs()
        self.assertEqual(freeze["content"]["archive_count"], 27_736)
        self.assertEqual(len(MODULE.membership_map(membership)), 78)
        self.assertEqual(len(MODULE.expected_blockers(summary)), 119)
        authorization = MODULE.authorization_matrix()
        self.assertTrue(authorization.pop("diagnostic_executed"))
        self.assertFalse(any(authorization.values()))

    def test_integer_timestamp_normalization_is_exact(self) -> None:
        milliseconds = "1582112100000"
        self.assertEqual(MODULE.normalize_timestamp_ms(milliseconds), int(milliseconds))
        self.assertEqual(
            MODULE.normalize_timestamp_ms(f"{milliseconds}000"), int(milliseconds)
        )
        self.assertEqual(
            MODULE.normalize_timestamp_ms("1582112399999999"), 1_582_112_399_999
        )
        for invalid in ("1582112100000.0", "-1", "1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(MODULE.DiagnosticMismatch):
                    MODULE.normalize_timestamp_ms(invalid)

    def test_three_orders_are_deterministic_and_complete(self) -> None:
        entries = [{"canonical_key": f"key-{index}"} for index in range(20)]
        normal = MODULE.source_order(entries, "normal")
        reverse = MODULE.source_order(entries, "reverse")
        shuffled = MODULE.source_order(entries, "deterministic_shuffled")
        self.assertEqual(reverse, list(reversed(normal)))
        self.assertEqual(
            shuffled, MODULE.source_order(entries, "deterministic_shuffled")
        )
        self.assertEqual(
            {item["canonical_key"] for item in normal},
            {item["canonical_key"] for item in shuffled},
        )

    def test_archive_binding_and_raw_row_provenance(self) -> None:
        open_time = 1_582_112_100_000
        close_time = open_time + 299_000
        with tempfile.TemporaryDirectory() as temporary:
            raw_root = Path(temporary)
            archive_path = (
                raw_root
                / "monthly/klines/AAAUSDT/5m/AAAUSDT-5m-2020-02.zip"
            )
            archive_path.parent.mkdir(parents=True)
            row = kline(open_time, close_time)
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("AAAUSDT-5m-2020-02.csv", row + "\n")
            payload = archive_path.read_bytes()
            entry = {
                "byte_size": len(payload),
                "canonical_key": (
                    "data/spot/monthly/klines/AAAUSDT/5m/"
                    "AAAUSDT-5m-2020-02.zip"
                ),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            rows = MODULE.inspect_archive(raw_root=raw_root, entry=entry)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["line_number"], 1)
            self.assertEqual(rows[0]["close_delta_ms"], 299_000)
            self.assertEqual(
                rows[0]["raw_row_sha256"], hashlib.sha256(row.encode()).hexdigest()
            )
            changed = dict(entry, byte_size=len(payload) + 1)
            with self.assertRaisesRegex(MODULE.DiagnosticMismatch, "binding drift"):
                MODULE.inspect_archive(raw_root=raw_root, entry=changed)

    def test_archive_member_identity_and_zip_failure_block(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            raw_root = Path(temporary)
            archive_path = (
                raw_root
                / "monthly/klines/AAAUSDT/5m/AAAUSDT-5m-2020-02.zip"
            )
            archive_path.parent.mkdir(parents=True)
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("wrong.csv", kline(1_582_112_100_000, 1_582_112_399_999))
            payload = archive_path.read_bytes()
            entry = {
                "byte_size": len(payload),
                "canonical_key": (
                    "data/spot/monthly/klines/AAAUSDT/5m/"
                    "AAAUSDT-5m-2020-02.zip"
                ),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            with self.assertRaisesRegex(MODULE.DiagnosticMismatch, "member identity"):
                MODULE.inspect_archive(raw_root=raw_root, entry=entry)

            bad = b"not-a-zip"
            archive_path.write_bytes(bad)
            entry.update(byte_size=len(bad), sha256=hashlib.sha256(bad).hexdigest())
            with self.assertRaisesRegex(MODULE.DiagnosticMismatch, "ZIP/CRC"):
                MODULE.inspect_archive(raw_root=raw_root, entry=entry)

    def test_synchronous_threshold_is_integer_and_membership_bound(self) -> None:
        members = {"2020-02": tuple(f"S{index:02d}" for index in range(15))}
        open_time = 1_582_112_100_000
        rows = [
            {"open_time_ms": open_time, "symbol": symbol}
            for symbol in members["2020-02"][:12]
        ]
        window = MODULE.synchronized_windows(rows, members)[0]
        self.assertTrue(window["synchronous_candidate"])
        self.assertEqual(window["synchronous_fraction"], "0.800000000000")
        window = MODULE.synchronized_windows(rows[:11], members)[0]
        self.assertFalse(window["synchronous_candidate"])
        with self.assertRaisesRegex(MODULE.DiagnosticMismatch, "non-member"):
            MODULE.synchronized_windows(
                rows + [{"open_time_ms": open_time, "symbol": "OUTSIDE"}], members
            )


if __name__ == "__main__":
    unittest.main()
