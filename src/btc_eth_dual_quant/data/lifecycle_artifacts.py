"""Canonical, hash-bound V4 lifecycle qualification artifacts."""
from __future__ import annotations

from typing import Any

from btc_eth_dual_quant.data.liquid_universe import canonical_hash


V4_MANIFEST_TYPES = {
    "source_manifest",
    "row_conflict_resolution_manifest",
    "lifecycle_policy_manifest",
    "lifecycle_resolution_registry",
    "symbol_availability_manifest",
    "active_universe_manifest",
    "complete_day_mask",
    "expected_grid_manifest",
    "raw_row_quarantine_manifest",
    "lifecycle_event_quarantine_manifest",
    "candidate_eligibility_manifest",
    "membership_manifest",
    "qualified_panel_manifest",
    "qualification_summary",
    "V3_V4_diff",
}


def make_v4_manifest(
    manifest_type: str,
    content: Any,
    *,
    contract_hash: str,
    lifecycle_registry_hash: str,
) -> dict[str, Any]:
    if manifest_type not in V4_MANIFEST_TYPES:
        raise ValueError("unknown V4 manifest type")
    document = {
        "schema_version": 4,
        "manifest_type": manifest_type,
        "contract_hash": contract_hash,
        "lifecycle_registry_hash": lifecycle_registry_hash,
        "content": content,
    }
    return {**document, "content_hash": canonical_hash(document)}
