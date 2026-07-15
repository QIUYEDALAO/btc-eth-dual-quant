#!/usr/bin/env python3
"""Offline verification for the frozen KLAYUSDT V3 adjudication evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from btc_eth_dual_quant.data.liquid_universe import canonical_hash, content_hash
from btc_eth_dual_quant.data.liquid_universe_pipeline import artifact_set_hash
from btc_eth_dual_quant.data.kline_row_conflicts import ResolutionRegistry
from scripts.liquid_universe_v3_klay_conflict_probe import (
    AFFECTED_ROW,
    BASELINE_HASHES,
    EXPECTED_DAILY_SHA256,
    EXPECTED_MONTHLY_SHA256,
    EXPECTED_ROW_SHA256,
    render_report,
    scan_forbidden_production_repairs,
    verify_document,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/m0/evidence/liquid_universe_v3/klay_source_conflict_adjudication.json"
REPORT = ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_KLAY_SOURCE_CONFLICT_ADJUDICATION_REPORT.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_baselines() -> list[str]:
    failures: list[str] = []
    contract = _load(ROOT / "config/liquid_spot_universe_contract_v3.json")
    registry_path = ROOT / "config/liquid_spot_source_conflict_resolutions_v3.json"
    registry = ResolutionRegistry.from_path(registry_path)
    adjudication = _load(ROOT / "reports/m0/evidence/liquid_universe_v2/source_conflict_adjudication.json")
    run = _load(ROOT / "reports/m0/evidence/liquid_universe_v3/requalification_run_manifest.json")
    source = _load(ROOT / "reports/m0/evidence/liquid_universe_v3/source_manifest.json")
    summary = _load(ROOT / "reports/m0/evidence/liquid_universe_v3/qualification_summary.json")
    actual = {
        "v3_contract": content_hash(contract),
        "resolution_registry": registry.canonical_hash,
        "btt_axs_adjudication_evidence": adjudication.get("content_hash"),
        "blocked_cold_artifact_set": artifact_set_hash(
            {
                name: {"content_hash": value}
                for name, value in run["content"]["builds"]["cold"]["manifest_hashes"].items()
            }
        ),
        "requalification_run_manifest": run.get("content_hash"),
        "source_manifest": source.get("content_hash"),
        "qualification_summary": summary.get("content_hash"),
    }
    for document, name in ((run, "run"), (source, "source"), (summary, "qualification"), (adjudication, "adjudication")):
        unsigned = {key: value for key, value in document.items() if key != "content_hash"}
        if document.get("content_hash") != canonical_hash(unsigned):
            failures.append(f"{name} content hash invalid")
    if actual != BASELINE_HASHES:
        failures.append(f"immutable baselines changed: {actual}")
    return failures


def validate() -> list[str]:
    failures = _verify_baselines()
    document = _load(EVIDENCE)
    failures.extend(verify_document(document))
    evidence = document.get("evidence", {})
    for name, expected in (("monthly_archive", EXPECTED_MONTHLY_SHA256), ("daily_archive", EXPECTED_DAILY_SHA256)):
        item = evidence.get(name, {})
        checksum_text = item.get("official_checksum_text", "")
        if checksum_text.split(maxsplit=1)[0].lower() != expected or item.get("current_remote_checksum") != expected:
            failures.append(f"{name} checksum binding mismatch")
        if item.get("zip_sha256") != expected or item.get("crc_valid") is not True or not item.get("zip_crc32"):
            failures.append(f"{name} archive integrity metadata mismatch")
        if item.get("affected_raw_fields") != AFFECTED_ROW:
            failures.append(f"{name} raw row changed")
        if canonical_hash(item.get("affected_raw_fields")) != EXPECTED_ROW_SHA256:
            failures.append(f"{name} raw row hash mismatch")
    for item in evidence.get("public_rest_comparators", []):
        payload = item.get("raw_payload_utf8", "").encode("utf-8")
        if hashlib.sha256(payload).hexdigest() != item.get("payload_sha256"):
            failures.append(f"{item.get('endpoint_identity')} payload hash mismatch")
        try:
            raw_rows = json.loads(payload)
        except json.JSONDecodeError:
            failures.append(f"{item.get('endpoint_identity')} payload is not JSON")
            continue
        normalized = [[str(value) for value in row] for row in raw_rows]
        if normalized != item.get("normalized_rows"):
            failures.append(f"{item.get('endpoint_identity')} normalized payload mismatch")
        if [canonical_hash(row) for row in normalized] != item.get("normalized_row_hashes"):
            failures.append(f"{item.get('endpoint_identity')} normalized row hash mismatch")
    lifecycle = evidence.get("symbol_lifecycle", {})
    normalized_lifecycle = {
        key: lifecycle[key]
        for key in (
            "article_code",
            "title",
            "public_url",
            "public_api_reference",
            "publication_time_utc",
            "effective_time_utc",
            "replacement_trading_time_utc",
            "affected_pairs",
            "relationship",
        )
    }
    if canonical_hash(normalized_lifecycle) != lifecycle.get("normalized_evidence_sha256"):
        failures.append("lifecycle normalized evidence hash mismatch")
    if REPORT.read_text(encoding="utf-8") != render_report(document):
        failures.append("Markdown report regeneration mismatch")
    failures.extend(scan_forbidden_production_repairs(ROOT / "src"))
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("LIQUID_UNIVERSE_V3_KLAY_CONFLICT_CHECK FAIL")
        for item in failures:
            print(f"- {item}")
        return 1
    document = _load(EVIDENCE)
    print("LIQUID_UNIVERSE_V3_KLAY_CONFLICT_CHECK PASS")
    print(f"classification={document['classification']}")
    print(f"decision={document['overall_decision']}")
    print(f"content_hash={document['content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
