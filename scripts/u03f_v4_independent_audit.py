#!/usr/bin/env python3
"""Run only the fixture smoke for the U-03F independent auditor implementation."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import (
    REQUIRED_AUDIT_ARTIFACTS,
    audit_artifact_set_hash,
    audit_manifest_hash,
    build_audit_artifacts,
)
from btc_eth_dual_quant.audit.liquid_universe_v4_independent import rank_membership


def fixture_smoke(order: str) -> dict:
    rows = [
        ("BTCUSDT", [Decimal("10")] * 90),
        ("ETHUSDT", [Decimal("9")] * 90),
    ]
    if order == "reverse":
        rows.reverse()
    membership = rank_membership("2024-01", dict(rows), target_size=2)
    contents = {name: [] if name.endswith("manifest") else {} for name in REQUIRED_AUDIT_ARTIFACTS}
    contents["membership_manifest"] = membership
    contents["qualification_summary"] = {
        "months": 1,
        "membership_rows": 2,
        "authorization": {"u04": False, "m2": False},
    }
    manifests = build_audit_artifacts(
        contents,
        contract_hash="fixture-contract",
        lifecycle_registry_hash="fixture-lifecycle-registry",
    )
    return {
        "mode": "fixture_only",
        "order": order,
        "artifact_set_hash": audit_artifact_set_hash(manifests),
        "manifest_hashes": {
            name: audit_manifest_hash(item)
            for name, item in sorted(manifests.items())
        },
        "full_public_audit_executed": False,
        "authorization": {"u04": False, "strategy": False, "oos": False, "m2": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-smoke", action="store_true")
    parser.add_argument("--order", choices=("normal", "reverse"), default="normal")
    args = parser.parse_args()
    if not args.fixture_smoke:
        parser.error("stage B permits --fixture-smoke only; the full public audit is not authorized")
    print(json.dumps(fixture_smoke(args.order), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
