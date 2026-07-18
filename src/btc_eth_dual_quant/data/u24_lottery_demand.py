"""Exact U-24 lottery-payoff statistic core for synthetic preflight and Paper work."""
from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from math import isfinite,log
from typing import Iterable,Sequence

HISTORY_HOURS=336
HALF_HOURS=168
MINIMUM_ACTIVE_MEMBERS=10
MAXIMUM_PEAK_RESIDUAL=log(1.08)
CLUSTER_MS=86_400_000

@dataclass(frozen=True)
class LotteryDecision:
    decision_ms:int
    symbols:Sequence[str]
    completed_log_returns:Sequence[Sequence[float]]
    path_displacements:Sequence[Sequence[float]]

def _exclusion_medians(values:Sequence[float])->tuple[float,...]:
    ordered=sorted((value,index) for index,value in enumerate(values));n=len(values)-1;left=(n-1)//2;right=n//2;out=[0.0]*len(values)
    positions={original:position for position,(_,original) in enumerate(ordered)}
    for original in range(len(values)):
        reduced=[ordered[position][0] for position in range(len(ordered)) if position!=positions[original]]
        out[original]=(reduced[left]+reduced[right])/2.0
    return tuple(out)

def evaluate_decision(row:LotteryDecision)->dict|None:
    count=len(row.symbols)
    if count<MINIMUM_ACTIVE_MEMBERS or len(set(row.symbols))!=count or len(row.completed_log_returns)!=count or len(row.path_displacements)!=count:return None
    if any(len(values)!=HISTORY_HOURS or any(not isfinite(value) for value in values) for values in row.completed_log_returns):return None
    if any(len(values)!=6 or any(not isfinite(value) for value in values) for values in row.path_displacements):return None
    residuals=[[] for _ in range(count)]
    for hour in range(HISTORY_HOURS):
        values=tuple(row.completed_log_returns[index][hour] for index in range(count));peers=_exclusion_medians(values)
        for index in range(count):residuals[index].append(values[index]-peers[index])
    scores=[]
    for index,symbol in enumerate(row.symbols):
        old=max(residuals[index][:HALF_HOURS]);new=max(residuals[index][HALF_HOURS:])
        scores.append((index,symbol,old,new))
    rank_count=(count+3)//4
    old_rank={symbol for _,symbol,_,_ in sorted(scores,key=lambda x:(x[2],x[1]))[:rank_count]}
    new_rank={symbol for _,symbol,_,_ in sorted(scores,key=lambda x:(x[3],x[1]))[:rank_count]}
    eligible=[value for value in scores if value[2]<=MAXIMUM_PEAK_RESIDUAL and value[3]<=MAXIMUM_PEAK_RESIDUAL and value[1] in old_rank and value[1] in new_rank]
    if not eligible:return None
    index,symbol,old,new=sorted(eligible,key=lambda x:(max(x[2],x[3]),x[2]+x[3],x[1]))[0]
    return {"decision_ms":row.decision_ms,"symbol":symbol,"old_half_peak_residual":f"{old:.12f}","new_half_peak_residual":f"{new:.12f}","path":tuple(f"{value:.12f}" for value in row.path_displacements[index])}

def evaluate_stream(rows:Iterable[LotteryDecision])->dict:
    groups=events=episodes=logical=0;prior_decision=None;prior_event=None;digest=hashlib.sha256()
    for row in rows:
        groups+=1;logical+=len(row.symbols)*HISTORY_HOURS
        if prior_decision is not None and row.decision_ms<=prior_decision:raise ValueError("decision order must be strictly increasing")
        prior_decision=row.decision_ms;event=evaluate_decision(row)
        if event is None:continue
        events+=1
        if prior_event is None or row.decision_ms-prior_event>CLUSTER_MS:episodes+=1;digest.update(json.dumps(event,sort_keys=True,separators=(",",":")).encode())
        prior_event=row.decision_ms
    return {"logical_hourly_member_returns":logical,"decision_groups":groups,"candidate_events":events,"independent_episodes":episodes,"event_digest":digest.hexdigest()}
