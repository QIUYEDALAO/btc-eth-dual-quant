#!/usr/bin/env python3
"""Check the committed M1G failed-IS evidence without runtime artifacts."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from m1g_is_protocol_check import load as load_protocol
from m1g_is_protocol_check import validate as validate_protocol


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/m1/M1G_IS_VALIDATION_REPORT.md"
BACKTEST = ROOT / "freqtrade_lab/scripts/ft_backtest_m1g_is.sh"


def main() -> int:
    failures = validate_protocol(load_protocol())
    text = REPORT.read_text(encoding="utf-8") if REPORT.is_file() else ""
    required = (
        "- Status: failed_validation",
        "- OOS opened: no",
        "- OOS prices/returns accessed: no",
        "| base | 179 | -22.6272% | -21.3551% |",
        "| cost_x2 | 177 | -28.3540% | -31.5286% |",
        "| Base native total return > 0 | fail |",
        "| Cost x2 conservative exit bar matches native | fail |",
        "- M1G OOS opening: no",
        "- M1H design review after this failure record merges: yes",
        "- M2: no",
    )
    for marker in required:
        if marker not in text:
            failures.append(f"IS report marker missing: {marker}")
    if len(re.findall(r"native/audited exit-bar mismatches=[1-9][0-9]*", text)) != 4:
        failures.append("all four conservative mismatch diagnostics must be non-zero and disclosed")

    ledger = yaml.safe_load((ROOT / "STRATEGY_TRIAL_LEDGER.yaml").read_text(encoding="utf-8"))
    candidates = [item for item in ledger["candidates"] if item["id"] == "M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION"]
    if len(candidates) != 1 or candidates[0].get("oos_opened") is not False:
        failures.append("M1G trial ledger must remain unique and OOS-unopened")
    backtest_text = BACKTEST.read_text(encoding="utf-8") if BACKTEST.is_file() else ""
    if "--timerange 20200701-20240911" not in backtest_text or "--cache none" not in backtest_text:
        failures.append("M1G IS runner must preserve the frozen IS range and disable cache")
    prohibited_command = "freqtrade " + "tr" + "ade"
    if prohibited_command in backtest_text:
        failures.append("M1G IS runner must not expose a trade command")

    if failures:
        print("m1g_is_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("m1g_is_check PASS")
    print("status=failed_validation oos_opened=no next=m1h_design_review_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
