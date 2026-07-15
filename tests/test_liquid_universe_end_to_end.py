import copy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from btc_eth_dual_quant.data.liquid_universe import DailyEvidence, MinuteBar
from btc_eth_dual_quant.data.liquid_universe_artifacts import render_qualification_report, write_manifest
from btc_eth_dual_quant.data.liquid_universe_pipeline import artifact_set_hash, build_artifacts
from scripts.liquid_universe_qualification_check import check

ROOT = Path(__file__).resolve().parents[1]
BASE_CONTRACT = json.loads((ROOT / "config/liquid_spot_universe_contract_v2.json").read_text())
REGISTRY = json.loads((ROOT / "config/liquid_spot_asset_eligibility_v2.json").read_text())
SHA = "a" * 64


def fixture():
    contract = copy.deepcopy(BASE_CONTRACT)
    contract["research_start"] = "2021-01-01"
    contract["frozen_end_month"] = "2021-01"
    contract["canonical_hash"] = "fixture-contract"
    start = date(2020, 1, 2)
    daily = []
    for symbol, quote in (("AAAUSDT", "100"), ("BBBUSDT", "90")):
        for index in range(365):
            daily.append(DailyEvidence(symbol, start + timedelta(days=index), Decimal(quote), "official_monthly_zip", SHA, Decimal("1"), Decimal("3"), Decimal("0.5"), Decimal("2"), Decimal("10")))
    month_start = datetime(2021, 1, 1, tzinfo=timezone.utc)
    bars = {}
    sources = []
    for symbol in ("AAAUSDT", "BBBUSDT"):
        rows = []
        for index in range(31 * 24 * 12):
            timestamp = month_start + timedelta(minutes=5 * index)
            rows.append(MinuteBar(symbol, timestamp, Decimal("1"), Decimal("3"), Decimal("0.5"), Decimal("2"), Decimal("1"), Decimal("2"), 1))
        bars[(symbol, "2021-01")] = rows
        sources.append({
            "canonical_key": f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-2021-01.zip",
            "canonical_url": "https://data.binance.vision/example",
            "symbol": symbol,
            "interval": "5m",
            "archive_month": "2021-01",
            "byte_size": 1,
            "sha256": SHA,
            "verification_status": "official_checksum_verified",
            "row_count": len(rows),
            "first_timestamp": rows[0].open_time.isoformat(),
            "last_timestamp": rows[-1].open_time.isoformat(),
            "authority_role": "official_monthly_zip_detail",
        })
    confirmed = {"schema_version": 2, "records": []}
    return contract, daily, bars, sources, confirmed


class LiquidUniverseEndToEndTests(unittest.TestCase):
    def test_fixture_rebuild_is_order_independent(self):
        contract, daily, bars, sources, confirmed = fixture()
        first = build_artifacts(contract=contract, registry=REGISTRY, confirmed_gap_registry=confirmed, daily=daily, bars_by_symbol_month=bars, source_rows=sources)
        reversed_bars = {key: list(reversed(value)) for key, value in reversed(list(bars.items()))}
        second = build_artifacts(contract=contract, registry=REGISTRY, confirmed_gap_registry=confirmed, daily=list(reversed(daily)), bars_by_symbol_month=reversed_bars, source_rows=list(reversed(sources)))
        self.assertEqual(artifact_set_hash(first), artifact_set_hash(second))
        self.assertEqual(first["qualification_summary"]["content"]["status"], "pass")

    def test_global_gap_quarantines_every_member(self):
        contract, daily, bars, sources, confirmed = fixture()
        missing = datetime(2021, 1, 10, 3, tzinfo=timezone.utc)
        for key in bars:
            bars[key] = [bar for bar in bars[key] if bar.open_time != missing]
        artifacts = build_artifacts(contract=contract, registry=REGISTRY, confirmed_gap_registry=confirmed, daily=daily, bars_by_symbol_month=bars, source_rows=sources)
        scopes = artifacts["quarantine_manifest"]["content"]["scopes"]
        self.assertEqual(scopes[0]["affected_symbols"], ["AAAUSDT", "BBBUSDT"])
        self.assertTrue(all(row["status"] == "global_window_quarantined" for row in artifacts["qualified_panel_manifest"]["content"]))

    def test_machine_artifacts_are_report_authority_and_tamper_is_detected(self):
        contract, daily, bars, sources, confirmed = fixture()
        artifacts = build_artifacts(contract=contract, registry=REGISTRY, confirmed_gap_registry=confirmed, daily=daily, bars_by_symbol_month=bars, source_rows=sources)
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "evidence"
            for name, document in artifacts.items():
                write_manifest(evidence / f"{name}.json", document)
            hashes = {name: document["content_hash"] for name, document in artifacts.items()}
            report = Path(temporary) / "report.md"
            report.write_text(render_qualification_report(artifacts["qualification_summary"]["content"], hashes))
            self.assertEqual(check(evidence, report, contract, REGISTRY), [])
            report.write_text(report.read_text().replace("Membership rows: 2", "Membership rows: 3"))
            self.assertIn("Markdown report does not match machine artifacts", check(evidence, report, contract, REGISTRY))

    def test_manifest_tamper_and_preregistered_binding_are_detected(self):
        contract, daily, bars, sources, confirmed = fixture()
        artifacts = build_artifacts(contract=contract, registry=REGISTRY, confirmed_gap_registry=confirmed, daily=daily, bars_by_symbol_month=bars, source_rows=sources)
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "evidence"
            for name, document in artifacts.items():
                write_manifest(evidence / f"{name}.json", document)
            report = Path(temporary) / "report.md"
            hashes = {name: document["content_hash"] for name, document in artifacts.items()}
            report.write_text(render_qualification_report(artifacts["qualification_summary"]["content"], hashes))
            membership_path = evidence / "membership_manifest.json"
            document = json.loads(membership_path.read_text())
            document["content"][0]["symbol"] = "EVILUSDT"
            membership_path.write_text(json.dumps(document))
            self.assertTrue(check(evidence, report, contract, REGISTRY))

    def test_gap_attribution_records_conserve_missing_slots(self):
        contract, daily, bars, sources, confirmed = fixture()
        missing = datetime(2021, 1, 10, 3, tzinfo=timezone.utc)
        for key in bars:
            bars[key] = [bar for bar in bars[key] if bar.open_time != missing]
        artifacts = build_artifacts(
            contract=contract,
            registry=REGISTRY,
            confirmed_gap_registry=confirmed,
            daily=daily,
            bars_by_symbol_month=bars,
            source_rows=sources,
        )
        records = artifacts["quarantine_manifest"]["content"]["attribution_records"]
        summary = artifacts["qualification_summary"]["content"]
        self.assertEqual(summary["gap_records"], len(records))
        self.assertEqual(summary["gap_missing_slots"], sum(row["missing_count"] for row in records))

    def test_tampered_confirmed_gap_registry_fails_closed(self):
        contract, daily, bars, sources, confirmed = fixture()
        confirmed["canonical_hash"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "confirmed-gap registry hash mismatch"):
            build_artifacts(
                contract=contract,
                registry=REGISTRY,
                confirmed_gap_registry=confirmed,
                daily=daily,
                bars_by_symbol_month=bars,
                source_rows=sources,
            )


if __name__ == "__main__":
    unittest.main()
