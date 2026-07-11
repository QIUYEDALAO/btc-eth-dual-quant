#!/usr/bin/env python3
"""Validate the sanitized gap-attribution report and its zero-unresolved gate."""
from pathlib import Path

PATH=Path('reports/m0/LIQUID_SPOT_UNIVERSE_GAP_ATTRIBUTION_REPORT.md')
def main():
    text=PATH.read_text()
    required=['- Status: pass_with_quarantine','- Original blocked symbol-months: 151','- Exact attributed gap runs: 227','- Unique Binance global outage windows: 15','- Binance global event runs: 225','- Symbol-specific archive gap runs: 2','- Processing errors: 0','- Unresolved gaps: 0','- Strategy design authorized: no','- Returns/backtest/OOS accessed: no','- M2 authorized: no','quarantine_isolate_symbol_month_without_replacement']
    failures=[f'missing marker: {x}' for x in required if x not in text]
    rows=[line for line in text.splitlines() if line.startswith('| ') and not line.startswith('| symbol') and not line.startswith('| ---')]
    if len(rows)!=227: failures.append(f'attribution row count {len(rows)} != 227')
    if 'blocked_unresolved' in '\n'.join(rows): failures.append('unresolved attribution row present')
    if failures:
        print('liquid_universe_gap_attribution_check FAIL')
        for item in failures: print(f'- {item}')
        return 1
    print('liquid_universe_gap_attribution_check PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
