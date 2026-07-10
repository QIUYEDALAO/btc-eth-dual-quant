"""Build a sanitized source-owner escalation package from M1E diagnostics."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping


TARGET_ISSUE = "https://github.com/binance/binance-public-data/issues/475"
ALREADY_COVERED_MONTH = "2020-12"


def build_package(evidence: Mapping[str, Any], generated_utc: str | None = None) -> dict[str, Any]:
    diagnostics = evidence.get("diagnostics")
    refetch = evidence.get("archive_refetch")
    if not isinstance(diagnostics, list) or not isinstance(refetch, list):
        raise ValueError("diagnostic evidence must contain diagnostics and archive_refetch lists")
    if evidence.get("contract_resolved") is not False or evidence.get("api_key_used") is not False:
        raise ValueError("source-owner package requires unresolved public-only evidence")

    covered = [item for item in diagnostics if item.get("month") == ALREADY_COVERED_MONTH]
    supplemental = [item for item in diagnostics if item.get("month") != ALREADY_COVERED_MONTH]
    rows = [
        {
            "symbol": str(item["symbol"]),
            "month": str(item["month"]),
            "timeframe": str(item["timeframe"]),
            "open_time": int(item["open_time"]),
            "differing_fields": list(item["differing_fields"]),
            "classification": str(item["classification"]),
            "rest_matches_official": bool(item["rest_matches_official"]),
            "rest_matches_derived": bool(item["rest_matches_derived"]),
            "derived_sha256": str(item["derived_sha256"]),
            "official_sha256": str(item["official_sha256"]),
            "rest_sha256": str(item["rest_sha256"]),
        }
        for item in sorted(supplemental, key=lambda item: (item["month"], item["symbol"], item["timeframe"], item["open_time"]))
    ]
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": 1,
        "generated_utc": generated_utc or datetime.now(timezone.utc).isoformat(),
        "status": "ready_not_submitted",
        "target_repository": "binance/binance-public-data",
        "target_issue": TARGET_ISSUE,
        "existing_issue_overlap_rows": len(covered),
        "supplemental_rows": len(rows),
        "supplemental_evidence_sha256": hashlib.sha256(canonical).hexdigest(),
        "monthly_zip_refetch_unchanged": sum(bool(item.get("unchanged")) for item in refetch),
        "monthly_zip_refetch_total": len(refetch),
        "rows": rows,
        "external_submission_performed": False,
        "api_key_used": False,
        "private_data_used": False,
        "raw_payload_included": False,
        "contract_resolved": False,
        "m2_authorized": False,
    }


def archive_url(row: Mapping[str, Any]) -> str:
    symbol, timeframe, month = row["symbol"], row["timeframe"], row["month"]
    return f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/{timeframe}/{symbol}-{timeframe}-{month}.zip"


def render_report(package: Mapping[str, Any]) -> str:
    rows = package["rows"]
    lines = [
        "# M1E Binance Source-Owner Escalation Package",
        "",
        "- Status: ready_not_submitted",
        f"- Target repository: `{package['target_repository']}`",
        f"- Existing issue: {package['target_issue']}",
        f"- Existing issue overlap rows: {package['existing_issue_overlap_rows']}",
        f"- New supplemental rows: {package['supplemental_rows']}",
        f"- Supplemental evidence SHA256: `{package['supplemental_evidence_sha256']}`",
        f"- Monthly ZIP refetch hashes unchanged: {package['monthly_zip_refetch_unchanged']}/{package['monthly_zip_refetch_total']}",
        "- External submission performed: no",
        "- API key used: no",
        "- Raw payload included: no",
        "- M1E contract resolved: no",
        "- M2 authorized: no",
        "",
        "## Routing Decision",
        "",
        "Binance issue #475 already documents the December 2020 monthly/daily/API disagreement. This package should be added as a comment to that issue instead of opening a duplicate. It contributes 14 non-December cross-timeframe cases from January 2021 through April 2022.",
        "",
        "## Supplemental Evidence",
        "",
        "| UTC open time | Symbol | TF | Fields | REST relationship | Classification | Monthly ZIP |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        utc = datetime.fromtimestamp(row["open_time"] / 1000, timezone.utc).isoformat()
        relation = "official" if row["rest_matches_official"] else "derived" if row["rest_matches_derived"] else "third version"
        lines.append(
            f"| {utc} | {row['symbol']} | {row['timeframe']} | {', '.join(row['differing_fields'])} "
            f"| REST matches {relation} | {row['classification']} | [ZIP]({archive_url(row)}) |"
        )
    lines += [
        "",
        "## Suggested Issue Comment",
        "",
        "```markdown",
        "I independently reproduced the monthly/daily/API inconsistency described here and found an additional cross-timeframe archive problem outside the December 2020 scope.",
        "",
        "Using BTCUSDT and ETHUSDT spot monthly kline ZIPs, I compared deterministic 12x5m -> 1h and 4x1h -> 4h aggregates with the published higher-timeframe ZIP rows, then checked the exact timestamps against current `GET /api/v3/klines`.",
        "",
        "Additional affected UTC timestamps:",
    ]
    unique = []
    for row in rows:
        label = f"- {datetime.fromtimestamp(row['open_time'] / 1000, timezone.utc).isoformat()} {row['symbol']} {row['timeframe']}: {row['classification']}"
        if label not in unique:
            unique.append(label)
    lines.extend(unique)
    lines += [
        "",
        f"All {package['monthly_zip_refetch_total']} affected monthly ZIPs were downloaded again and retained the same SHA-256 hashes. The supplemental evidence contains {package['supplemental_rows']} conflict rows with SHA-256 `{package['supplemental_evidence_sha256']}`.",
        "",
        "The differences are in volume, quote volume, trade count, and taker-volume fields; OHLC prices are equal for these supplemental cross-timeframe cases. REST supports the published higher timeframe in 10 rows, the child aggregation in 2 rows, and a third value in 2 rows.",
        "",
        "Could Binance clarify whether kline archives at different intervals are expected to be arithmetically consistent, and which source is canonical when the child aggregate, higher-timeframe monthly ZIP, and current API disagree?",
        "```",
        "",
        "## Submission Boundary",
        "",
        "This package is prepared but was not posted externally. Posting requires an explicit user decision. Regardless of any comment, M1E remains blocked until Binance corrects or documents the conflicting sources and the project reruns its fixed Gate.",
        "",
    ]
    return "\n".join(lines)
