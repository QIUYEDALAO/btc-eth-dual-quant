#!/usr/bin/env python3
"""Attribute every selected-universe 5m gap from ignored official ZIPs."""
from __future__ import annotations
import csv, hashlib, io, json, re, zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from btc_eth_dual_quant.data.universe_gap_attribution import classify_missing_slots, gate
from liquid_universe_public_run import archive_timestamp

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/m0/LIQUID_SPOT_UNIVERSE_QUALIFICATION_REPORT.md'
OUT=ROOT/'reports/m0/LIQUID_SPOT_UNIVERSE_GAP_ATTRIBUTION_REPORT.md'
STORE=ROOT/'storage/raw/liquid_universe/data/spot/monthly/klines'

def members():
    result={}
    for line in REPORT.read_text().splitlines():
        match=re.match(r"- (\d{4}-\d{2}): (.+)",line)
        if match: result[match.group(1)]=match.group(2).split(', ')
    return result

def next_month(ts):
    return datetime(ts.year+(ts.month==12),1 if ts.month==12 else ts.month+1,1,tzinfo=timezone.utc)

def read_times(symbol, month):
    path=STORE/symbol/'5m'/f'{symbol}-5m-{month}.zip'
    if not path.exists(): return set(), f'official_monthly_zip_missing:{path.name}', []
    errors=[]; times=[]
    try:
        with zipfile.ZipFile(path) as z:
            name=next(x for x in z.namelist() if x.endswith('.csv'))
            for row in csv.reader(io.TextIOWrapper(z.open(name),encoding='utf-8')):
                if not row or not row[0].isdigit(): continue
                ts=archive_timestamp(row[0])
                if ts.second or ts.microsecond or ts.minute%5: errors.append(f'{symbol}:{month}:off_grid:{ts.isoformat()}')
                times.append(ts)
    except Exception as exc: errors.append(f'{symbol}:{month}:archive_error:{type(exc).__name__}')
    if len(times)!=len(set(times)): errors.append(f'{symbol}:{month}:duplicate_timestamp')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    return set(times), f'official_monthly_zip_sha256={digest}', errors

def main():
    contract=json.loads((ROOT/'config/liquid_spot_universe_contract.json').read_text())
    policy=contract['gap_handling_policy']; universe=members(); missing_by_month={}; sources={}; processing=[]
    for month,symbols in universe.items():
        start=datetime.fromisoformat(month+'-01T00:00:00+00:00'); end=next_month(start)
        expected=set(); cur=start
        while cur<end: expected.add(cur); cur+=timedelta(minutes=5)
        for symbol in symbols:
            actual,source,errors=read_times(symbol,month); sources[(symbol,month)]=source; processing+=errors
            missing_by_month[(symbol,month)]=expected-actual
    records=[]
    for month,symbols in universe.items():
        slot_map=defaultdict(set)
        for symbol in symbols:
            for ts in missing_by_month[(symbol,month)]: slot_map[ts].add(symbol)
        for symbol in symbols:
            records += classify_missing_slots(symbol=symbol,month=month,missing=missing_by_month[(symbol,month)],
                missing_by_slot=slot_map,member_count=len(symbols),evidence_source=sources[(symbol,month)],policy=policy)
    status,unresolved=gate(records,processing)
    global_n=sum(r.classification=='binance_global_event' for r in records)
    symbol_n=sum(r.classification=='symbol_specific_archive_gap' for r in records)
    global_windows=len({(r.month,r.timestamp,r.missing_count) for r in records if r.classification=='binance_global_event'})
    incomplete_symbol_hours=sum(len({ts.replace(minute=0,second=0,microsecond=0) for ts in missing}) for missing in missing_by_month.values())
    expected_symbol_hours=0
    for month,symbols in universe.items():
        start=datetime.fromisoformat(month+'-01T00:00:00+00:00'); expected_symbol_hours += int((next_month(start)-start).total_seconds()//3600)*len(symbols)
    complete_symbol_hours=expected_symbol_hours-incomplete_symbol_hours
    lines=['# Liquid Spot Universe Gap Attribution Report','',f'- Status: {status}',f'- Original blocked symbol-months: 151',f'- Exact attributed gap runs: {len(records)}',f'- Unique Binance global outage windows: {global_windows}',f'- Binance global event runs: {global_n}',f'- Symbol-specific archive gap runs: {symbol_n}',f'- Complete derived 1h symbol-bars: {complete_symbol_hours}',f'- Quarantined incomplete 1h symbol-bars: {incomplete_symbol_hours}',f'- Processing errors: {len(processing)}',f'- Unresolved gaps: {unresolved}','- Strategy design authorized: no','- Returns/backtest/OOS accessed: no','- M2 authorized: no','','## Attribution','', '| symbol | month | timestamp UTC | missing_count | duration | classification | evidence_source | qualification_decision |','| --- | --- | --- | ---: | ---: | --- | --- | --- |']
    for r in records:
        lines.append(f'| {r.symbol} | {r.month} | {r.timestamp.isoformat()} | {r.missing_count} | {r.duration_minutes}m | {r.classification} | {r.evidence_source} | {r.qualification_decision} |')
    lines += ['','## Processing Errors',''] + ([f'- {x}' for x in processing] or ['- none'])
    OUT.write_text('\n'.join(lines)+'\n')
    print(f'status={status} runs={len(records)} global={global_n} symbol={symbol_n} processing={len(processing)} unresolved={unresolved}')
    return 0 if status=='pass_with_quarantine' else 2
if __name__=='__main__': raise SystemExit(main())
