from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.u04_cross_sectional_data_qualification import (
    EVIDENCE,
    QualificationFailure,
    SealedOOSAccess,
    _verify_authority_content,
    _verify_manifest_hashes,
    content_hash,
    identity_hash,
    load_json,
    ordered,
    require_is_open_time,
    verify_archive,
)
from scripts.u04_cross_sectional_data_qualification_check import validate as validate_result


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/u04_cross_sectional_data_qualification_v1.json"
RESULT = ROOT / "reports/m1/evidence/u04_cross_sectional_data_qualification_v1.json"
REPORT = ROOT / "reports/m1/U04_CROSS_SECTIONAL_DATA_QUALIFICATION.md"


class U04CrossSectionalDataQualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_json(CONFIG)

    def test_contract_hash_excludes_generation_time(self):
        self.assertEqual(content_hash(self.config), self.config["content_hash"])
        changed = copy.deepcopy(self.config)
        changed["generated_utc"] = "2099-01-01T00:00:00Z"
        self.assertEqual(content_hash(changed), self.config["content_hash"])

    def test_only_data_qualification_is_authorized(self):
        auth = self.config["authorizations"]
        self.assertTrue(auth["frozen_source_identity_verification"])
        self.assertTrue(auth["data_qualification"])
        self.assertTrue(auth["isolation_gate_implementation"])
        for key in ("event_scan", "residual_or_mad", "path_observation", "formal_returns", "strategy", "backtesting", "oos", "api_trading", "execution_live", "m2"):
            self.assertFalse(auth[key], key)

    def test_is_boundary_fails_before_oos_decode(self):
        contract = self.config["isolation_contract"]
        require_is_open_time(0 + 1577836800000, contract)
        require_is_open_time(1726012799999, contract)
        with self.assertRaises(SealedOOSAccess):
            require_is_open_time(1726012800000, contract)
        with self.assertRaises(SealedOOSAccess):
            require_is_open_time(1726012800001, contract)
        with self.assertRaises(QualificationFailure):
            require_is_open_time(1577836799999, contract)

    def test_frozen_manifest_authorities_are_exact(self):
        hashes = _verify_manifest_hashes(self.config)
        self.assertEqual(len(hashes), 19)
        self.assertEqual(hashes["membership_manifest"], self.config["authority_bindings"]["membership_manifest_hash"])
        self.assertEqual(hashes["expected_grid_manifest"], self.config["authority_bindings"]["expected_grid_manifest_hash"])
        self.assertEqual(hashes["qualified_panel_manifest"], self.config["authority_bindings"]["qualified_panel_manifest_hash"])

    def test_grid_membership_panel_and_mask_accounting_are_exact(self):
        self.assertEqual(
            _verify_authority_content(self.config),
            {"membership_rows": 1170, "months": 78, "grid_rows": 1170, "panel_rows": 1170},
        )

    def test_archive_identity_crc_and_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key = "data/spot/monthly/klines/AAAUSDT/5m/AAAUSDT-5m-2020-01.zip"
            path = root / key
            path.parent.mkdir(parents=True)
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("AAAUSDT-5m-2020-01.csv", "1,2,3\n")
            payload = path.read_bytes()
            binding = {"canonical_key": key, "byte_size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            self.assertEqual(verify_archive(root, binding), binding)
            bad = dict(binding, sha256="0" * 64)
            with self.assertRaises(QualificationFailure):
                verify_archive(root, bad)

    def test_unsafe_or_missing_archive_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for key in ("../escape.zip", "/absolute.zip", "not-a-zip.csv"):
                with self.assertRaises(QualificationFailure):
                    verify_archive(root, {"canonical_key": key, "byte_size": 0, "sha256": "0" * 64})

    def test_three_orders_have_one_canonical_identity(self):
        rows = [
            {"canonical_key": f"data/{index}.zip", "byte_size": index, "sha256": str(index) * 64}
            for index in range(1, 8)
        ]
        identities = []
        for order in self.config["source_verification"]["traversal_orders"]:
            traversal = ordered(rows, order, self.config["source_verification"]["deterministic_shuffle_seed"])
            identities.append(identity_hash(sorted(traversal, key=lambda item: (item["canonical_key"], item["sha256"], item["byte_size"]))))
        self.assertEqual(len(set(identities)), 1)

    def test_authority_or_permission_tamper_changes_contract_identity(self):
        for path, value in (
            (("authority_bindings", "source_freeze_hash"), "0" * 64),
            (("isolation_contract", "oos_ohlc_decode_allowed"), True),
            (("authorizations", "event_scan"), True),
            (("data_authority_gates", "minimum_active_members"), 9),
        ):
            changed = copy.deepcopy(self.config)
            changed[path[0]][path[1]] = value
            self.assertNotEqual(content_hash(changed), self.config["content_hash"])

    def test_committed_result_is_exact_and_passes(self):
        result = load_json(RESULT)
        self.assertEqual(validate_result(self.config, result, REPORT.read_text(encoding="utf-8")), [])
        self.assertEqual(result["qualification_content_hash"], "4bdebb527494386d43f85189bf835e7fa1426325c5ef5383ec6fa46c2bb55a8c")

    def test_result_tamper_fails(self):
        result = load_json(RESULT)
        for path, value in (
            (("isolation", "oos_opened"), True),
            (("isolation", "oos_ohlc_values_decoded"), 1),
            (("counts", "manifests_exact"), 18),
            (("authorizations", "strategy"), True),
        ):
            changed = copy.deepcopy(result)
            changed[path[0]][path[1]] = value
            changed["qualification_content_hash"] = identity_hash({key: item for key, item in changed.items() if key != "qualification_content_hash"})
            self.assertTrue(validate_result(self.config, changed, REPORT.read_text(encoding="utf-8")), path)


if __name__ == "__main__":
    unittest.main()
