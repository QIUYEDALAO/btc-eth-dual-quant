from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.u04_cross_sectional_data_qualification import QualificationFailure, SealedOOSAccess, load_json, require_is_open_time, verify_archive
from scripts.u05_cross_sectional_data_qualification import git_json, verify_four_hour_authority
from scripts.u05_cross_sectional_data_qualification_check import CONFIG, EXPECTED_RESULT_HASH, REPORT, RESULT, validate


class U05CrossSectionalDataQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_json(CONFIG)

    def test_exact_protocol_target_is_available_and_sealed(self) -> None:
        protocol = git_json(self.config["protocol_target_commit"], "config/u05_cross_sectional_paper_protocol_v1.json")
        self.assertEqual(protocol["content_hash"], self.config["protocol_content_hash"])
        self.assertFalse(protocol["scope"]["oos_opened"])

    def test_four_hour_authority_is_aligned_and_complete(self) -> None:
        counts = verify_four_hour_authority(self.config)
        self.assertGreater(counts["expected_4h_member_blocks"], 0)
        self.assertEqual(counts["expected_4h_member_blocks"] * 4, counts["constituent_1h_rows"])

    def test_is_boundary_fails_before_oos_decode(self) -> None:
        contract = self.config["isolation_contract"]
        require_is_open_time(1577836800000, contract)
        require_is_open_time(1726012799999, contract)
        with self.assertRaises(SealedOOSAccess):
            require_is_open_time(1726012800000, contract)
        with self.assertRaises(QualificationFailure):
            require_is_open_time(1577836799999, contract)

    def test_archive_identity_crc_and_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key = "data/spot/monthly/klines/AAAUSDT/5m/AAAUSDT-5m-2020-01.zip"
            path = root / key
            path.parent.mkdir(parents=True)
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("AAAUSDT-5m-2020-01.csv", "1,2,3\n")
            payload = path.read_bytes()
            binding = {"canonical_key": key, "byte_size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            self.assertEqual(verify_archive(root, binding), binding)
            with self.assertRaises(QualificationFailure):
                verify_archive(root, dict(binding, sha256="0" * 64))

    def test_permissions_and_grid_tamper_fail_identity(self) -> None:
        from scripts.u04_cross_sectional_data_qualification import content_hash
        self.assertEqual(content_hash(self.config), self.config["content_hash"])
        for section, key, value in (
            ("authorizations", "event_scan", True),
            ("isolation_contract", "oos_ohlc_decode_allowed", True),
            ("signal_grid_contract", "constituent_bars_per_signal", 3),
            ("data_authority_gates", "minimum_active_members", 9),
        ):
            changed = copy.deepcopy(self.config); changed[section][key] = value
            self.assertNotEqual(content_hash(changed), self.config["content_hash"])

    def test_committed_result_is_exact(self) -> None:
        result = load_json(RESULT)
        self.assertEqual(result["qualification_content_hash"], EXPECTED_RESULT_HASH)
        self.assertEqual(validate(self.config, result, REPORT.read_text(encoding="utf-8")), [])

    def test_result_tamper_fails(self) -> None:
        from scripts.u04_cross_sectional_data_qualification import identity_hash
        result = load_json(RESULT)
        for section, key, value in (
            ("isolation", "oos_opened", True),
            ("isolation", "breadth_rows_generated", 1),
            ("counts", "manifests_exact", 18),
            ("authorizations", "strategy", True),
        ):
            changed = copy.deepcopy(result); changed[section][key] = value
            changed["qualification_content_hash"] = identity_hash({k: v for k, v in changed.items() if k != "qualification_content_hash"})
            self.assertTrue(validate(self.config, changed, REPORT.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
