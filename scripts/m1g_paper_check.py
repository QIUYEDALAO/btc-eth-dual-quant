#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "config" / "m1g_is_paper_protocol.json"
REPORT = ROOT / "reports" / "m1" / "M1G_IS_PAPER_FEASIBILITY_REPORT.md"
LEDGER = ROOT / "STRATEGY_TRIAL_LEDGER.yaml"
EXPECTED_PROTOCOL_HASH = "b77feb6725ee80837f67a56513a67bf7f305ea043dc81f4087c762fc4a61e91d"


def failures() -> list[str]:
    result: list[str] = []
    if hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != EXPECTED_PROTOCOL_HASH:
        result.append("frozen M1G protocol hash changed")
    text = REPORT.read_text(encoding="utf-8")
    required = (
        "- Status: pass", "- Complete events: 210", "- Projected full events: 300",
        "- Projected sealed-OOS events: 90", "- Combined median 24h MFE: 2.6908%",
        "- Combined median 24h MAE: -3.3118%", "- Worst 24h MAE: -21.5829%",
        "| combined_median_mfe | pass |", "| each_symbol_median_mfe | pass |",
        "- Formal strategy returns computed: no", "- Equity curve computed: no",
        "- OOS prices/returns accessed: no", "- OOS opened: no",
        "- Strategy code authorized: no", "- Freqtrade backtesting authorized: no",
        "- M2 authorized: no", "Paper pass does not establish positive expectancy",
    )
    result.extend(f"report missing {marker!r}" for marker in required if marker not in text)
    ledger = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    matches = [item for item in ledger.get("candidates", []) if item.get("id") == "M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION"]
    if len(matches) != 1 or matches[0].get("status") != "declared_unopened" or matches[0].get("oos_opened") is not False:
        result.append("M1G trial must remain declared_unopened with sealed OOS")
    return result


def main() -> int:
    result = failures()
    if result:
        print("m1g_paper_check FAIL")
        for failure in result:
            print(f"- {failure}")
        return 1
    print("m1g_paper_check PASS")
    print("status=pass_tail_risk_disclosed next=fixed_rule_contract oos_opened=no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
