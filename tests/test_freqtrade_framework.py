from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from btc_eth_dual_quant.data.storage import AppendOnlyRawStore


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from freqtrade_data_provenance import compare_provenance, render_report
from freqtrade_runtime_manifest import REQUIRED_COMMANDS, validate_manifest


class FreqtradeRuntimeTests(unittest.TestCase):
    def test_pinned_manifest_matches_compose_and_approved_commands(self) -> None:
        self.assertEqual(validate_manifest(), [])
        manifest = json.loads((ROOT / "freqtrade_lab" / "runtime-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["command_categories"]), REQUIRED_COMMANDS)
        self.assertIn("2026.6@sha256:", manifest["image_ref"])

    def test_manifest_rejects_version_or_digest_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = json.loads((ROOT / "freqtrade_lab" / "runtime-manifest.json").read_text(encoding="utf-8"))
            manifest["digest"] = "sha256:" + "0" * 64
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            failures = validate_manifest(manifest_path, ROOT / "freqtrade_lab" / "docker-compose.yml")
        self.assertTrue(any("digest" in failure for failure in failures))

    def test_unified_research_entry_has_only_approved_commands(self) -> None:
        source = (ROOT / "freqtrade_lab" / "scripts" / "ft_research.sh").read_text(encoding="utf-8")
        for command in REQUIRED_COMMANDS:
            self.assertIn(command, source)
        self.assertIn("Configuration error", source)
        forbidden = "freqtrade " + "tr" + "ade"
        self.assertNotIn(forbidden, source)


class FreqtradeProvenanceTests(unittest.TestCase):
    def test_matching_public_json_and_m0_raw_pass(self) -> None:
        rows = [
            [0, "100.0", "110", "90", "105", "10", 86_399_999],
            [86_400_000, "105", "115", "95", "110", "11", 172_799_999],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_root = root / "raw"
            AppendOnlyRawStore(raw_root).append(
                "spot_klines",
                "fixture",
                "GET public klines",
                {"symbol": "BTCUSDT", "interval": "1d"},
                rows,
            )
            freqtrade_path = root / "BTC_USDT-1d.json"
            freqtrade_path.write_text(json.dumps([row[:6] for row in rows]), encoding="utf-8")
            result = compare_provenance("BTCUSDT", "1d", freqtrade_path, raw_root)
            report = render_report([result])
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.overlap_rows, 2)
        self.assertIn("- Status: pass", report)

    def test_provenance_blocks_field_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw_root = root / "raw"
            AppendOnlyRawStore(raw_root).append(
                "spot_klines",
                "fixture",
                "GET public klines",
                {"symbol": "ETHUSDT", "interval": "1d"},
                [[0, "100", "110", "90", "105", "10", 86_399_999]],
            )
            freqtrade_path = root / "ETH_USDT-1d.json"
            freqtrade_path.write_text(json.dumps([[0, "100", "110", "90", "106", "10"]]), encoding="utf-8")
            result = compare_provenance("ETHUSDT", "1d", freqtrade_path, raw_root)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.field_differences, 1)


if __name__ == "__main__":
    unittest.main()
