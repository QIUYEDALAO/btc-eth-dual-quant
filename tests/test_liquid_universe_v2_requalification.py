import copy
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.liquid_universe_public_run import _daily_rows
from scripts.liquid_universe_public_run import _diagnostic_deduplicate
from btc_eth_dual_quant.data.liquid_universe import DailyEvidence
from scripts.liquid_universe_v2_requalification import (
    assert_deterministic,
    membership_diff,
    parse_v1_membership,
    render_diff_report,
)
from scripts.liquid_universe_v2_requalification_check import check as requalification_check


class LiquidUniverseV2RequalificationTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.contract = json.loads((root / "config/liquid_spot_universe_contract_v2.json").read_text())
        self.registry = json.loads((root / "config/liquid_spot_asset_eligibility_v2.json").read_text())

    def test_v1_parser_is_historical_diff_input_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "v1.md"
            path.write_text("# Historical\n\n- 2020-01: BTCUSDT, ETHUSDT\n", encoding="utf-8")
            self.assertEqual(parse_v1_membership(path), {"2020-01": ["BTCUSDT", "ETHUSDT"]})

    def test_membership_diff_is_deterministic(self):
        old = {"2025-06": ["USD1USDT", "BTCUSDT", "ETHUSDT"]}
        new = {"2025-06": ["BTCUSDT", "ETHUSDT", "JUPUSDT"]}
        result = membership_diff(old, new)
        self.assertEqual(result["membership_additions"], 1)
        self.assertEqual(result["membership_removals"], 1)
        self.assertEqual(result["details"][0]["added"], ["JUPUSDT"])
        self.assertEqual(result["details"][0]["removed"], ["USD1USDT"])
        self.assertEqual(render_diff_report(result), render_diff_report(copy.deepcopy(result)))

    def test_cold_warm_hash_mismatch_blocks(self):
        cold = {"a": {"content_hash": "one"}}
        warm = {"a": {"content_hash": "two"}}
        with self.assertRaisesRegex(ValueError, "deterministic mismatch"):
            assert_deterministic(cold, warm)

    def test_no_strategy_or_trading_authority(self):
        source = Path("scripts/liquid_universe_v2_requalification.py").read_text(encoding="utf-8")
        for forbidden in ("freqtrade backtesting", "create_order", "cancel_order", "place_order", "execution/live"):
            self.assertNotIn(forbidden, source)

    def test_invalid_excluded_fiat_row_is_recorded_but_crypto_row_blocks(self):
        row = "1605225600000,0.71859000,0.72033000,0.71479000,0.72216000,1,0,1,1,1,1,0\n"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "row.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("row.csv", row)
            source = {"sha256": "a" * 64, "canonical_key": "aud"}
            self.assertEqual(_daily_rows(path, "AUDUSDT", "2020-11", source, "official_monthly_zip", self.contract, self.registry), [])
            self.assertEqual(source["excluded_invalid_daily_rows"][0]["exclusion_category"], "fiat_pegged")
            with self.assertRaisesRegex(ValueError, "OHLC ordering"):
                _daily_rows(path, "JUPUSDT", "2020-11", {"sha256": "a" * 64, "canonical_key": "jup"}, "official_monthly_zip", self.contract, self.registry)

    def test_blocked_merge_diagnostic_dedup_is_deterministic(self):
        row = DailyEvidence(
            "AXSUSDT", date(2026, 2, 10), Decimal("1"), "official_monthly_zip",
            "a" * 64, Decimal("1"), Decimal("2"), Decimal("0.5"), Decimal("1.5"),
            Decimal("10"), "archive",
        )
        self.assertEqual(_diagnostic_deduplicate([row, row]), [row])

    def test_committed_blocked_evidence_is_exact_and_fail_closed(self):
        root = Path(__file__).resolve().parents[1]
        failures = requalification_check(
            root / "reports/m0/evidence/liquid_universe_v2",
            root / "reports/m0/LIQUID_SPOT_UNIVERSE_V2_QUALIFICATION_REPORT.md",
            root / "reports/m0/LIQUID_SPOT_UNIVERSE_V1_V2_DIFF_REPORT.md",
        )
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
