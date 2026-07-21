#!/usr/bin/env python3
"""Fail-closed IS preflight for point-in-time membership exit execution.

This checker reads only frozen manifest metadata plus an optional already-built
IS materialization manifest.  It never reads OOS price rows and never runs a
strategy.  A membership interval may end only when the source freeze contains
the next boundary 5m archive needed to execute a still-open position without a
synthetic price or a forward search.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IS_END_MONTH = "2024-09"
IS_END_EXCLUSIVE = "2024-09-11T00:00:00Z"
EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_runtime/is_boundary_qualification.json"


def canonical_hash(value: dict[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def byte_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def next_month(value: str) -> str:
    current = datetime.strptime(value, "%Y-%m").replace(tzinfo=timezone.utc)
    if current.month == 12:
        return current.replace(year=current.year + 1, month=1).strftime("%Y-%m")
    return current.replace(month=current.month + 1).strftime("%Y-%m")


def build(root: Path, materialization: dict[str, Any] | None) -> dict[str, Any]:
    source_path = root / "reports/m0/evidence/liquid_universe_v4/source_freeze_manifest.json"
    membership_path = root / "reports/m0/evidence/liquid_universe_v4_adr0015_requalification/membership_manifest.json"
    causal_path = root / "reports/m1/evidence/external_strategy_runtime/causal_summary.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    membership = json.loads(membership_path.read_text(encoding="utf-8"))
    causal = json.loads(causal_path.read_text(encoding="utf-8"))
    catalog = {row["canonical_key"]: row for row in source["content"]["archives"]}

    active: dict[str, set[str]] = {}
    for row in membership["content"]:
        month = row["effective_month"][:7]
        if "2020-01" <= month <= IS_END_MONTH and row["eligibility_status"] == "qualified":
            active.setdefault(row["symbol"], set()).add(month)

    transitions: list[dict[str, Any]] = []
    for symbol, months in sorted(active.items()):
        for month in sorted(months):
            boundary_month = next_month(month)
            if boundary_month in months or boundary_month > IS_END_MONTH:
                continue
            boundary = f"{boundary_month}-01T00:00:00Z"
            if boundary >= IS_END_EXCLUSIVE:
                continue
            archive = f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{boundary_month}.zip"
            frozen = catalog.get(archive)
            transitions.append({
                "symbol": symbol,
                "last_active_month": month,
                "membership_end_exclusive": boundary,
                "required_boundary_archive": archive,
                "frozen_boundary_archive": frozen is not None,
                "frozen_boundary_archive_sha256": None if frozen is None else frozen["sha256"],
                "frozen_boundary_archive_size": None if frozen is None else frozen["byte_size"],
            })

    missing = [row for row in transitions if not row["frozen_boundary_archive"]]
    materialization_identity = None
    if materialization is not None:
        materialization_identity = {
            "schema_version": materialization.get("schema_version"),
            "status": materialization.get("status"),
            "content_hash": materialization.get("content_hash"),
            "symbol_count": materialization.get("symbol_count"),
            "archive_count": len(materialization.get("archives", [])),
            "file_count": len(materialization.get("files", [])),
            "market_rows_decoded": materialization.get("market_rows_decoded"),
            "oos_rows_decoded": materialization.get("oos_rows_decoded"),
        }

    blocked = bool(missing)
    result = {
        "schema_version": "external-strategy-is-boundary-qualification-v1",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "blocked_data_authority_missing_membership_exit_open" if blocked else "pass",
        "source_freeze_hash": source["content_hash"],
        "source_freeze_byte_sha256": byte_hash(source_path),
        "membership_manifest_hash": membership["content_hash"],
        "membership_manifest_byte_sha256": byte_hash(membership_path),
        "causal_summary_hash": causal["content_hash"],
        "causal_pass_count": causal["pass_count"],
        "minimum_causal_pass_count": causal["minimum_required_before_is"],
        "membership_exit_execution_rule": "first_exact_5m_open_at_membership_end_exclusive",
        "boundary_transition_count": len(transitions),
        "frozen_boundary_archive_count": len(transitions) - len(missing),
        "missing_frozen_boundary_archive_count": len(missing),
        "transitions": transitions,
        "is_materialization": materialization_identity,
        "failure_reason": (
            "A position may remain open when a point-in-time member exits. The frozen source authority has no "
            "5m archive at any of the required exit boundaries, so the exit cannot use a real exact-boundary open."
            if blocked else None
        ),
        "forbidden_remedies": [
            "synthetic_or_last_price_exit",
            "forward_search_for_later_open",
            "unfrozen_source_archive",
            "future_membership_lookahead_exit",
            "current_member_backfill",
        ],
        "is_authorized": not blocked,
        "is_trials_materialized": 0,
        "selection_trial_count": 0,
        "oos_authorized": False,
        "oos_opened": False,
        "oos_runs": 0,
        "oos_rows_decoded": 0,
        "dry_run_bot": False,
        "api_live": False,
        "m2": False,
    }
    result["content_hash"] = canonical_hash(result)
    return result


def validate(root: Path, evidence: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expected = build(root, None)
    for key in (
        "status", "source_freeze_hash", "source_freeze_byte_sha256", "membership_manifest_hash",
        "membership_manifest_byte_sha256", "causal_summary_hash", "causal_pass_count",
        "minimum_causal_pass_count", "membership_exit_execution_rule", "boundary_transition_count",
        "frozen_boundary_archive_count", "missing_frozen_boundary_archive_count", "transitions",
        "failure_reason", "forbidden_remedies", "is_authorized", "is_trials_materialized",
        "selection_trial_count", "oos_authorized", "oos_opened", "oos_runs", "oos_rows_decoded",
        "dry_run_bot", "api_live", "m2",
    ):
        if evidence.get(key) != expected.get(key):
            failures.append(f"boundary qualification drift: {key}")
    materialization = evidence.get("is_materialization")
    if not isinstance(materialization, dict):
        failures.append("IS materialization identity missing")
    else:
        if materialization.get("status") != "pass" or materialization.get("oos_rows_decoded") != 0:
            failures.append("IS materialization isolation failed")
        if materialization.get("market_rows_decoded", 0) <= 0:
            failures.append("IS materialization row accounting missing")
        if materialization.get("content_hash") != "628bec95afbce9fb63d6a20a0d9047b09d611d87bd645680e17069e5d2c39def":
            failures.append("IS materialization identity drift")
    if evidence.get("content_hash") != canonical_hash(evidence):
        failures.append("boundary qualification content hash mismatch")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--materialization-manifest", type=Path)
    args = parser.parse_args()
    if args.write:
        if args.materialization_manifest is None:
            raise SystemExit("--materialization-manifest is required with --write")
        materialization = json.loads(args.materialization_manifest.read_text(encoding="utf-8"))
        evidence = build(ROOT, materialization)
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    failures = validate(ROOT, evidence)
    if failures:
        print("external strategy IS boundary qualification FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "external strategy IS boundary qualification BLOCKED-VALID: "
        f"missing={evidence['missing_frozen_boundary_archive_count']}/"
        f"{evidence['boundary_transition_count']} is=0 oos=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
