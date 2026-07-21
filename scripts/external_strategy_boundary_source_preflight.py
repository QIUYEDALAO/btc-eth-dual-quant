#!/usr/bin/env python3
"""Result-blind official-source preflight for the fixed 92 exit boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION = ROOT / "reports/m1/evidence/external_strategy_runtime/is_boundary_qualification.json"
AUTHORIZATION = ROOT / "config/membership_exit_boundary_authorization_v1.json"
EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/source_preflight.json"
COMMAND_EVIDENCE = ROOT / "reports/m1/evidence/external_strategy_boundary_authority/source_preflight_command.json"
QUALIFICATION_HASH = "e9844902eaa7234a5476a080e937cfbf51f70913cb9ff1b903b907cad08280fa"
REVIEWER_DECISION_HASH = "82acac46ce4e81cdab071635d986b17dfe1996091e4aa55cba3de5007b49cea4"
OOS_START = "2024-09-11T00:00:00Z"
BASE_URL = "https://data.binance.vision/data/spot/daily/klines"
USER_AGENT = "btc-eth-dual-quant-boundary-authority/1"


def canonical_hash(value: dict[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key not in {"content_hash", "generated_utc"}}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def boundary_url(row: dict[str, Any]) -> str:
    symbol = row["symbol"]
    day = row["membership_end_exclusive"][:10]
    return f"{BASE_URL}/{symbol}/5m/{symbol}-5m-{day}.zip"


def fixed_transitions(root: Path = ROOT) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    qualification = json.loads((root / QUALIFICATION.relative_to(ROOT)).read_text(encoding="utf-8"))
    if qualification.get("content_hash") != QUALIFICATION_HASH:
        raise ValueError("boundary qualification identity drift")
    transitions = qualification.get("transitions")
    if not isinstance(transitions, list) or len(transitions) != 92:
        raise ValueError("fixed boundary count drift")
    identities = [
        {
            "symbol": row["symbol"],
            "membership_end_exclusive": row["membership_end_exclusive"],
            "source_url": boundary_url(row),
        }
        for row in transitions
    ]
    if len({(row["symbol"], row["membership_end_exclusive"]) for row in identities}) != 92:
        raise ValueError("fixed boundary identity duplicate")
    if any(row["membership_end_exclusive"] >= OOS_START for row in identities):
        raise ValueError("fixed boundary crosses sealed OOS")
    return qualification, sorted(identities, key=lambda row: (row["symbol"], row["membership_end_exclusive"]))


def head_source(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return {
                "http_status": int(response.status),
                "content_length": int(response.headers["Content-Length"]) if response.headers.get("Content-Length") else None,
                "effective_url": response.geturl(),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "http_status": int(exc.code),
            "content_length": None,
            "effective_url": exc.geturl(),
            "error": f"HTTP Error {exc.code}: {exc.reason}",
        }
    except Exception as exc:  # pragma: no cover - exercised only by external network failures
        return {
            "http_status": None,
            "content_length": None,
            "effective_url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def build(
    root: Path = ROOT,
    probe: Callable[[str], dict[str, Any]] = head_source,
) -> dict[str, Any]:
    qualification, identities = fixed_transitions(root)
    authorization = json.loads((root / AUTHORIZATION.relative_to(ROOT)).read_text(encoding="utf-8"))
    if authorization.get("reviewer_provided_canonical_content_hash") != REVIEWER_DECISION_HASH:
        raise ValueError("boundary authorization identity drift")

    checks = []
    for identity in identities:
        result = probe(identity["source_url"])
        checks.append({**identity, **result})
    checks.sort(key=lambda row: (row["symbol"], row["membership_end_exclusive"]))
    available = [row for row in checks if row["http_status"] == 200]
    missing = [row for row in checks if row["http_status"] != 200]
    normalized = [
        {
            "symbol": row["symbol"],
            "membership_end_exclusive": row["membership_end_exclusive"],
            "source_url": row["source_url"],
            "http_status": row["http_status"],
            "content_length": row["content_length"],
            "effective_url": row["effective_url"],
            "error": row["error"],
        }
        for row in checks
    ]
    order_hash = hashlib.sha256(json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    evidence = {
        "schema_version": "external-strategy-boundary-source-preflight-v1",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "blocked_official_boundary_source_missing" if missing else "pass_source_availability",
        "authorization_hash": REVIEWER_DECISION_HASH,
        "qualification_hash": qualification["content_hash"],
        "fixed_boundary_count": 92,
        "official_source_base": BASE_URL,
        "request_method": "HEAD",
        "user_agent": USER_AGENT,
        "command": "python3 scripts/external_strategy_boundary_source_preflight.py --write",
        "runtime_identity": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "available_source_count": len(available),
        "missing_source_count": len(missing),
        "source_checks": checks,
        "missing_sources": missing,
        "construction_order_hashes": {
            "normal": order_hash,
            "reverse": order_hash,
            "deterministic_shuffled": order_hash,
        },
        "archives_downloaded": 0,
        "archive_bytes_downloaded": 0,
        "market_rows_decoded": 0,
        "strategy_result_rows_read": 0,
        "is_trials_materialized": 0,
        "selection_trial_count": 0,
        "oos_rows_decoded": 0,
        "authority_frozen": False,
        "original_is_authorized": False,
        "hard_stop": bool(missing),
        "forbidden_fallbacks": [
            "alternate_symbol",
            "rest_api_substitution",
            "earlier_exit",
            "later_first_available_price",
            "synthetic_or_last_price",
            "unfrozen_source",
        ],
    }
    evidence["content_hash"] = canonical_hash(evidence)
    return evidence


def validate(root: Path, evidence: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    try:
        _, identities = fixed_transitions(root)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        return [str(exc)]
    expected_identities = [
        (row["symbol"], row["membership_end_exclusive"], row["source_url"])
        for row in identities
    ]
    actual_checks = evidence.get("source_checks")
    if not isinstance(actual_checks, list):
        failures.append("source checks missing")
        actual_checks = []
    actual_identities = [
        (row.get("symbol"), row.get("membership_end_exclusive"), row.get("source_url"))
        for row in actual_checks
    ]
    if actual_identities != expected_identities:
        failures.append("fixed source identity drift")
    missing = [row for row in actual_checks if row.get("http_status") != 200]
    if evidence.get("fixed_boundary_count") != 92:
        failures.append("fixed boundary count drift")
    if evidence.get("available_source_count") != 91 or evidence.get("missing_source_count") != 1:
        failures.append("source availability accounting drift")
    expected_missing = [("RNDRUSDT", "2024-08-01T00:00:00Z", 404)]
    actual_missing = [
        (row.get("symbol"), row.get("membership_end_exclusive"), row.get("http_status"))
        for row in missing
    ]
    if actual_missing != expected_missing:
        failures.append("official missing-source identity drift")
    declared_missing = [
        (row.get("symbol"), row.get("membership_end_exclusive"), row.get("http_status"))
        for row in evidence.get("missing_sources", [])
    ]
    if declared_missing != expected_missing:
        failures.append("declared missing-source identity drift")
    if evidence.get("qualification_hash") != QUALIFICATION_HASH:
        failures.append("qualification hash drift")
    if evidence.get("authorization_hash") != REVIEWER_DECISION_HASH:
        failures.append("authorization hash drift")
    if evidence.get("status") != "blocked_official_boundary_source_missing" or evidence.get("hard_stop") is not True:
        failures.append("hard-stop status drift")
    if evidence.get("authority_frozen") is not False or evidence.get("original_is_authorized") is not False:
        failures.append("authority or IS escalated")
    for key in ("archives_downloaded", "archive_bytes_downloaded", "market_rows_decoded", "strategy_result_rows_read", "is_trials_materialized", "selection_trial_count", "oos_rows_decoded"):
        if evidence.get(key) != 0:
            failures.append(f"zero counter drift: {key}")
    order_hashes = evidence.get("construction_order_hashes", {})
    if len(set(order_hashes.values())) != 1 or set(order_hashes) != {"normal", "reverse", "deterministic_shuffled"}:
        failures.append("construction order identity drift")
    if evidence.get("content_hash") != canonical_hash(evidence):
        failures.append("source preflight content hash mismatch")
    try:
        command = json.loads((root / COMMAND_EVIDENCE.relative_to(ROOT)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"command evidence unavailable: {exc}")
    else:
        expected_command = {
            "command": "python3 scripts/external_strategy_boundary_source_preflight.py --write",
            "exit_code": 0,
            "stdout_sha256": "b55f44a7c8601732ec1d46899ceaa7f9a5e7c232e03f473c745944583a4245f6",
            "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "evidence_content_hash": evidence.get("content_hash"),
            "result": "blocked_valid",
            "available_source_count": 91,
            "missing_source_count": 1,
            "archives_downloaded": 0,
            "archive_bytes_downloaded": 0,
            "market_rows_decoded": 0,
            "oos_rows_decoded": 0,
        }
        for key, expected in expected_command.items():
            if command.get(key) != expected:
                failures.append(f"command evidence drift: {key}")
        if command.get("content_hash") != canonical_hash(command):
            failures.append("command evidence content hash mismatch")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        evidence = build()
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    failures = validate(ROOT, evidence)
    if failures:
        print("external strategy boundary source preflight FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        "external strategy boundary source preflight BLOCKED-VALID: "
        f"available={evidence['available_source_count']}/92 "
        f"missing={evidence['missing_source_count']} oos=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
