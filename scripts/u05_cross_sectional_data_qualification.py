#!/usr/bin/env python3
"""Qualify U-05 frozen V4 authority without decoding events, paths, or OOS OHLC."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.u04_cross_sectional_data_qualification import (
    EVIDENCE,
    QualificationFailure,
    _verify_authority_content,
    _verify_manifest_hashes,
    content_hash,
    identity_hash,
    load_json,
    ordered,
    require_is_open_time,
    verify_archive,
)


PROTOCOL_PATH = "config/u05_cross_sectional_paper_protocol_v1.json"
REVIEW_PATH = ROOT / "reports/expert/evidence/u05_cross_sectional_paper_protocol_review_v1.json"


def git_json(commit: str, rel_path: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "show", f"{commit}:{rel_path}"], cwd=ROOT,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise QualificationFailure(f"exact target unavailable: {commit}:{rel_path}")
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise QualificationFailure("target JSON root is not an object")
    return value


def verify_four_hour_authority(config: Mapping[str, Any]) -> dict[str, int]:
    signal = config["signal_grid_contract"]
    if signal != {
        "signal_timeframe": "4h",
        "completed_block_alignment": "utc_blocks_ending_at_00_04_08_12_16_20",
        "constituent_timeframe": "1h",
        "constituent_bars_per_signal": 4,
        "path_timeframe": "5m",
        "complete_constituent_set_required": True,
        "quarantined_constituent_action": "entire_4h_signal_block_ineligible",
        "later_block_substitution_allowed": False,
    }:
        raise QualificationFailure("4h signal-grid contract drift")
    panel = load_json(EVIDENCE / "qualified_panel_manifest.json")["content"]
    expected_4h = 0
    quarantined_1h = 0
    for row in panel:
        expected = int(row["expected_1h_count"])
        valid = int(row["valid_1h_count"])
        quarantined = int(row["quarantined_1h_count"])
        if expected % 4 or valid + quarantined != expected:
            raise QualificationFailure("1h authority cannot support aligned completed 4h blocks")
        expected_4h += expected // 4
        quarantined_1h += quarantined
    return {
        "expected_4h_member_blocks": expected_4h,
        "constituent_1h_rows": sum(int(row["expected_1h_count"]) for row in panel),
        "quarantined_1h_rows": quarantined_1h,
    }


def _verify_named_bindings(config: Mapping[str, Any], hashes: Mapping[str, str]) -> None:
    bindings = config["authority_bindings"]
    mapping = {
        "membership_manifest_hash": "membership_manifest",
        "expected_grid_manifest_hash": "expected_grid_manifest",
        "qualified_panel_manifest_hash": "qualified_panel_manifest",
        "complete_day_mask_hash": "complete_day_mask",
        "invalid_interval_slot_mask_hash": "invalid_interval_slot_mask_manifest",
        "invalid_interval_accounting_hash": "invalid_interval_accounting_manifest",
    }
    for binding, manifest in mapping.items():
        if bindings[binding] != hashes[manifest]:
            raise QualificationFailure(f"authority binding drift: {binding}")


def qualify(*, raw_root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if content_hash(config) != config.get("content_hash"):
        raise QualificationFailure("qualification contract hash drift")
    protocol = git_json(str(config["protocol_target_commit"]), PROTOCOL_PATH)
    review = load_json(REVIEW_PATH)
    if protocol.get("content_hash") != config["protocol_content_hash"]:
        raise QualificationFailure("target protocol binding drift")
    for key in ("membership_authority_hash", "lifecycle_registry_hash"):
        if protocol.get("authority_bindings", {}).get(key) != config["authority_bindings"].get(key):
            raise QualificationFailure(f"protocol authority binding drift: {key}")
    if review.get("review_content_hash") != config["protocol_review_content_hash"]:
        raise QualificationFailure("protocol review binding drift")
    if review.get("verdict") != "approve" or review.get("remaining_critical_findings") != 0 or review.get("remaining_high_findings") != 0:
        raise QualificationFailure("protocol review is not approve 0/0")

    manifest_hashes = _verify_manifest_hashes(config)
    _verify_named_bindings(config, manifest_hashes)
    counts = _verify_authority_content(config)
    four_hour = verify_four_hour_authority(config)
    freeze = load_json(EVIDENCE / "source_freeze_manifest.json")
    if identity_hash(freeze["content"]) != config["authority_bindings"]["source_freeze_hash"]:
        raise QualificationFailure("source-freeze content drift")
    archives = freeze["content"]["archives"]
    if len(archives) != config["authority_bindings"]["source_archive_count"]:
        raise QualificationFailure("source archive count drift")

    source = config["source_verification"]
    verified = [verify_archive(raw_root, binding) for binding in ordered(archives, "normal", source["deterministic_shuffle_seed"])]
    order_rows = []
    for order in source["traversal_orders"]:
        traversal = ordered(verified, order, source["deterministic_shuffle_seed"])
        canonical = sorted(traversal, key=lambda item: (item["canonical_key"], item["sha256"], item["byte_size"]))
        order_rows.append({"order": order, "content_identity_hash": identity_hash(canonical), "archive_count": len(canonical)})
    if len({row["content_identity_hash"] for row in order_rows}) != 1:
        raise QualificationFailure("source traversal identity mismatch")

    result = {
        "schema_version": 1,
        "qualification_id": config["qualification_id"],
        "status": "pass",
        "contract_content_hash": config["content_hash"],
        "protocol_target_commit": config["protocol_target_commit"],
        "protocol_content_hash": config["protocol_content_hash"],
        "protocol_review_content_hash": config["protocol_review_content_hash"],
        "source_freeze_hash": config["authority_bindings"]["source_freeze_hash"],
        "v4_artifact_set_hash": config["authority_bindings"]["v4_artifact_set_hash"],
        "manifest_hashes": manifest_hashes,
        "orders": order_rows,
        "counts": {**counts, **four_hour, "archive_count": len(verified), "manifests_exact": len(manifest_hashes)},
        "isolation": {
            "is_start": config["isolation_contract"]["is_start"],
            "is_end_exclusive": config["isolation_contract"]["is_end_exclusive"],
            "oos_opened": False,
            "oos_archive_access": "opaque_identity_and_crc_only",
            "oos_ohlc_values_decoded": 0,
            "breadth_rows_generated": 0,
            "event_rows_generated": 0,
            "path_rows_generated": 0,
            "return_rows_generated": 0,
        },
        "authorizations": {
            "one_sealed_is_paper_observation": True,
            "event_scan_beyond_one_frozen_is_observation": False,
            "strategy": False, "backtesting": False, "oos": False,
            "api_trading": False, "execution_live": False, "m2": False,
        },
        "network_accessed": False,
        "production_evidence_mutated": False,
    }
    result["qualification_content_hash"] = identity_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config/u05_cross_sectional_data_qualification_v1.json")
    parser.add_argument("--raw-root", type=Path, default=ROOT / "storage/raw/liquid_universe")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/m1/evidence/u05_cross_sectional_data_qualification_v1.json")
    args = parser.parse_args()
    result = qualify(raw_root=args.raw_root, config=load_json(args.config))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"U-05 data qualification PASS archives={result['counts']['archive_count']} hash={result['qualification_content_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
