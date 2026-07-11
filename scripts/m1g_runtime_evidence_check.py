#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate(payload: dict) -> list[str]:
    failures: list[str] = []
    expected = {
        "version": 1,
        "status": "pass",
        "candidate_id": "M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION",
        "runtime": "freqtrade 2026.6",
        "image_digest": "sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6",
        "timerange": "20200701-20240911",
        "public_data_only": True,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            failures.append(f"runtime evidence changed: {key}")
    if payload.get("lookahead_analysis") != {
        "status": "pass", "total_signals": 20, "biased_entry_signals": 0,
        "biased_exit_signals": 0, "biased_indicators": [],
    }:
        failures.append("lookahead evidence is not the frozen passing result")
    if payload.get("recursive_analysis") != {
        "status": "pass", "startup_candles": [170, 250, 340],
        "indicator_variance_found": False, "indicator_lookahead_found": False,
    }:
        failures.append("recursive evidence is not the frozen passing result")
    for key in ("performance_report_generated", "oos_accessed", "api_key_used", "runtime_artifacts_committed"):
        if payload.get(key) is not False:
            failures.append(f"runtime safety flag must remain false: {key}")
    return failures


def main() -> int:
    payload = json.loads((ROOT / "config/m1g_runtime_evidence.json").read_text(encoding="utf-8"))
    failures = validate(payload)
    if failures:
        print("m1g_runtime_evidence_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1g_runtime_evidence_check PASS")
    print("lookahead=pass recursive=pass performance_backtest=no oos=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
