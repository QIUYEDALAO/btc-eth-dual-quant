#!/usr/bin/env python3
"""Convert Freqtrade list-data output into sanitized T2 runtime evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.data.golden_data import (
    FREQTRADE_IMAGE_REF,
    FREQTRADE_VERSION,
    parse_freqtrade_list_data,
    validate_freqtrade_runtime_evidence,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record sanitized Freqtrade T2 list-data evidence")
    parser.add_argument("--input", required=True, help="Ignored raw list-data output")
    parser.add_argument("--out", default="storage/logs/t2_freqtrade_runtime_evidence.json")
    args = parser.parse_args()
    raw = Path(args.input).read_text(encoding="utf-8")
    entries = [asdict(item) for item in parse_freqtrade_list_data(raw)]
    evidence = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "image_ref": FREQTRADE_IMAGE_REF,
        "version": FREQTRADE_VERSION,
        "command": "list-data",
        "data_format": "jsongz",
        "note": "Pinned Freqtrade 2026.6 container read all six BTC/ETH 1m, 5m, and 15m caches with exact ranges and row counts.",
        "entries": entries,
        "output_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "api_key_used": False,
        "private_data_used": False,
        "runtime_data_committed": False,
    }
    if FREQTRADE_VERSION not in raw or not validate_freqtrade_runtime_evidence(evidence):
        raise SystemExit("Freqtrade runtime output does not match the frozen T2 cache manifest")
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"evidence={output}")
    print("status=pass entries=6 api_key_used=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
