#!/usr/bin/env python3
"""Run the ADR-0011 public-archive qualification. No strategy outcomes."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, urllib.parse, urllib.request, zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET

from btc_eth_dual_quant.data.liquid_universe import DailyEvidence, MinuteBar, aggregate_one_hour, build_month, membership_hash

BUCKET="https://data.binance.vision"
S3="https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
ROOT=Path(__file__).resolve().parents[1]

def archive_timestamp(value):
    raw=int(value)
    return datetime.fromtimestamp(raw/(1_000_000 if raw>=10**15 else 1_000),timezone.utc)

def list_keys(prefix):
    token=None; out=[]
    while True:
        q={"list-type":"2","prefix":prefix,"max-keys":"1000"}
        if token: q["continuation-token"]=token
        root=ET.fromstring(urllib.request.urlopen(S3+"?"+urllib.parse.urlencode(q),timeout=60).read())
        ns={"s":"http://s3.amazonaws.com/doc/2006-03-01/"}
        out += [x.text for x in root.findall("s:Contents/s:Key",ns)]
        node=root.find("s:NextContinuationToken",ns)
        if node is None: return out
        token=node.text

def list_prefixes(prefix):
    token=None; out=[]; ns={"s":"http://s3.amazonaws.com/doc/2006-03-01/"}
    while True:
        q={"list-type":"2","prefix":prefix,"delimiter":"/","max-keys":"1000"}
        if token: q["continuation-token"]=token
        root=ET.fromstring(urllib.request.urlopen(S3+"?"+urllib.parse.urlencode(q),timeout=60).read())
        out += [x.text for x in root.findall("s:CommonPrefixes/s:Prefix",ns)]
        node=root.find("s:NextContinuationToken",ns)
        if node is None: return out
        token=node.text

def fetch(key, store):
    path=store/key; path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        data=urllib.request.urlopen(f"{BUCKET}/{urllib.parse.quote(key)}",timeout=90).read()
        path.write_bytes(data)
    return path

def csv_rows(path):
    with zipfile.ZipFile(path) as z:
        name=next(x for x in z.namelist() if x.endswith('.csv'))
        return list(csv.reader(io.TextIOWrapper(z.open(name),encoding='utf-8')))

def month_iter(start,end):
    cur=start
    while cur<=end:
        yield cur
        cur=date(cur.year+(cur.month==12),1 if cur.month==12 else cur.month+1,1)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--end-month',default='2026-06'); ap.add_argument('--workers',type=int,default=12); args=ap.parse_args()
    end=date.fromisoformat(args.end_month+'-01'); contract=json.loads((ROOT/'config/liquid_spot_universe_contract.json').read_text())
    store=ROOT/'storage/raw/liquid_universe'; prefix='data/spot/monthly/klines/'
    symbol_prefixes=[]
    for p in list_prefixes(prefix):
        symbol=p.rstrip('/').split('/')[-1]
        if symbol.isascii() and symbol.isalnum() and symbol.endswith('USDT'): symbol_prefixes.append(p)
    keys=[]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for result in ex.map(lambda p: list_keys(p+'1d/'),symbol_prefixes): keys.extend(result)
    daily={}
    for k in keys:
        parts=k.split('/')
        if len(parts)>=7 and parts[5]=='1d' and parts[4].endswith('USDT') and k.endswith('.zip'):
            ym=Path(k).stem.rsplit('-',2)[-2]+'-'+Path(k).stem.rsplit('-',2)[-1]
            try: md=date.fromisoformat(ym+'-01')
            except ValueError: continue
            if date(2019,1,1)<=md<=end: daily[(parts[4],ym)]=k
    paths={}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures={ex.submit(fetch,k,store):key for key,k in daily.items()}
        for f,key in futures.items(): paths[key]=f.result()
    evidence=[]
    for (symbol,ym),path in paths.items():
        h=hashlib.sha256(path.read_bytes()).hexdigest()
        for r in csv_rows(path):
            if not r or not r[0].isdigit(): continue
            evidence.append(DailyEvidence(symbol,archive_timestamp(r[0]).date(),Decimal(r[7]),'monthly',h))
    snapshots=[]
    for month in month_iter(date(2020,1,1),end): snapshots.extend(build_month(month,evidence,contract))
    needed={(r.symbol,r.effective_month[:7]) for r in snapshots}; five={}; five_keys=[]
    selected_symbols=sorted({s for s,_ in needed})
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        prefixes=[prefix+s+'/5m/' for s in selected_symbols]
        for result in ex.map(list_keys,prefixes): five_keys.extend(result)
    for k in five_keys:
        p=k.split('/')
        if len(p)>=7 and p[5]=='5m' and k.endswith('.zip'):
            ym=Path(k).stem[-7:]
            if (p[4],ym) in needed: five[(p[4],ym)]=k
    five_paths={}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures={ex.submit(fetch,k,store):key for key,k in five.items()}
        for f,key in futures.items(): five_paths[key]=f.result()
    blockers=[]; qualified=0; derived=0
    for key in sorted(needed):
        path=five_paths.get(key)
        if not path: blockers.append(f"{key[0]}:{key[1]} missing 5m archive"); continue
        rows=csv_rows(path); bars=[]
        try:
            for r in rows:
                if not r or not r[0].isdigit(): continue
                bars.append(MinuteBar(key[0],archive_timestamp(r[0]),*(Decimal(r[i]) for i in (1,2,3,4,5))))
            grouped=defaultdict(list)
            for b in bars: grouped[b.open_time.replace(minute=0,second=0,microsecond=0)].append(b)
            for group in grouped.values(): aggregate_one_hour(group); derived+=1
            qualified+=1
        except ValueError as e: blockers.append(f"{key[0]}:{key[1]} {e}")
    by_month=defaultdict(list)
    for r in snapshots: by_month[r.effective_month[:7]].append(r)
    status='pass' if not blockers and by_month else 'blocked'
    report=['# Liquid Spot Universe Qualification Report','',f'- Status: {status}',f'- Actual range: 2020-01-01 through {args.end_month}-30',f'- Historical symbols discovered: {len({x.symbol for x in evidence})}',f'- Monthly memberships: {len(by_month)}',f'- Membership rows: {len(snapshots)}',f'- Qualified 5m symbol-months: {qualified}',f'- Derived 1h bars: {derived}',f'- Blockers: {len(blockers)}',f'- Membership hash: {membership_hash(snapshots)}','- Strategy/events/signals/returns computed: no','- OOS accessed: no',f'- Strategy design authorized: {"yes" if status=="pass" else "no"}','- M2 authorized: no','- Runtime artifacts committed: no','','## Monthly Top 15','']
    for m,rs in sorted(by_month.items()): report.append(f'- {m}: '+', '.join(x.symbol for x in rs))
    report += ['','## Blockers',''] + ([f'- {x}' for x in blockers] or ['- none'])
    (ROOT/'reports/m0/LIQUID_SPOT_UNIVERSE_QUALIFICATION_REPORT.md').write_text('\n'.join(report)+'\n')
    print(f'status={status} symbols={len({x.symbol for x in evidence})} months={len(by_month)} blockers={len(blockers)}')
    return 0 if status=='pass' else 2
if __name__=='__main__': raise SystemExit(main())
