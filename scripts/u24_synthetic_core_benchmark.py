#!/usr/bin/env python3
from __future__ import annotations
import json,resource,time
from btc_eth_dual_quant.data.u24_lottery_demand import HISTORY_HOURS,LotteryDecision,evaluate_stream
DECISIONS=199;MEMBERS=15;LOGICAL_ROWS=DECISIONS*MEMBERS*HISTORY_HOURS
def fixture():
 symbols=tuple(f"S{i:02d}USDT" for i in range(MEMBERS));paths=tuple(tuple(0.001*h for h in (1,2,4,8,12,24)) for _ in symbols)
 histories=[]
 for member in range(MEMBERS):histories.append(tuple(((hour*17+member*7)%31-15)*0.0002+(0.00005*member) for hour in range(HISTORY_HOURS)))
 completed=tuple(histories)
 for decision in range(DECISIONS):yield LotteryDecision(decision*14_400_000,symbols,completed,paths)
def main()->int:
 started=time.perf_counter();result=evaluate_stream(fixture());elapsed=time.perf_counter()-started;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024 if __import__('sys').platform!='darwin' else 1024*1024)
 payload={"elapsed_seconds":f"{elapsed:.6f}","peak_rss_mib":f"{rss:.3f}","minimum_logical_hourly_member_returns":1000000,"actual_logical_hourly_member_returns":LOGICAL_ROWS,"maximum_elapsed_seconds":30,"maximum_peak_rss_mib":1024,"result":result};payload["pass"]=LOGICAL_ROWS>=1000000 and elapsed<=30 and rss<=1024 and result["logical_hourly_member_returns"]==LOGICAL_ROWS and result["candidate_events"]==DECISIONS
 print(json.dumps(payload,sort_keys=True,separators=(",",":")));return 0 if payload["pass"] else 1
if __name__=="__main__":raise SystemExit(main())
