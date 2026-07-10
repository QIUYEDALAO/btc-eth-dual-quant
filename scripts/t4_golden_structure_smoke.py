#!/usr/bin/env python3
"""Profile ignored T2 golden 15m data without selecting research events."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".deps"))
sys.path.insert(0, str(ROOT / "src"))

from btc_eth_dual_quant.audit.feasibility import profile_golden_15m


def main() -> int:
    parser = argparse.ArgumentParser(description="T4 golden 15m structural smoke")
    parser.add_argument("--golden-root", type=Path, default=ROOT / "storage/duckdb/t2_golden")
    parser.add_argument("--out", type=Path, default=ROOT / "storage/logs/t4_golden_structure_smoke.json")
    args = parser.parse_args()
    profiles = []
    for symbol in ("BTCUSDT", "ETHUSDT"):
        path = args.golden_root / f"{symbol}-15m.jsonl.gz"
        rows = []
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                rows.append(json.loads(line))
        profiles.append({"symbol": symbol, **asdict(profile_golden_15m(rows))})
    evidence = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "pass",
        "profiles": profiles,
        "candidate_events_selected": False,
        "candidate_returns_computed": False,
        "oos_returns_accessed": False,
        "api_key_used": False,
        "runtime_artifacts_committed": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"evidence={args.out}")
    print("status=pass symbols=2 candidate_events_selected=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
