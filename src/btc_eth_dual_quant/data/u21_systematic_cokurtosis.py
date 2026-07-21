"""U-21 systematic-cokurtosis evaluator shared by preflight and Paper work."""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from math import ceil, isfinite
from typing import Iterable, Sequence

@dataclass(frozen=True)
class CokurtosisCandidatePath:
    decision_ms:int; symbol:str; candidate_returns:Sequence[float]; peer_common_returns:Sequence[float]; path_displacements:Sequence[float]

def half_cokurtosis(candidate_returns:Sequence[float], common_returns:Sequence[float])->float|None:
    if len(candidate_returns)!=168 or len(common_returns)!=168:return None
    sx=sy=sx2=sy2=sxy=sx2y=sxy2=sx2y2=0.0
    for candidate,common in zip(candidate_returns,common_returns):
        x=candidate-common
        if not isfinite(x) or not isfinite(common):return None
        x2=x*x; y2=common*common
        sx+=x; sy+=common; sx2+=x2; sy2+=y2; sxy+=x*common
        sx2y+=x2*common; sxy2+=x*y2; sx2y2+=x2*y2
    n=168.0; a=sx/n; b=sy/n; ex2=sx2/n; ey2=sy2/n
    vx=ex2-a*a; vy=ey2-b*b
    if not isfinite(vx) or not isfinite(vy) or vx<=0 or vy<=0:return None
    comoment=(sx2y2/n-2*b*(sx2y/n)+b*b*ex2-2*a*(sxy2/n)+4*a*b*(sxy/n)-2*a*b*b*a+a*a*ey2-2*a*a*b*b+a*a*b*b)
    value=comoment/(vx*vy)
    return value if isfinite(value) else None

def candidate_statistics(row:CokurtosisCandidatePath)->dict|None:
    if len(row.candidate_returns)!=336 or len(row.peer_common_returns)!=336 or len(row.path_displacements)!=6:return None
    if any(not isfinite(v) for v in row.path_displacements):return None
    first=half_cokurtosis(row.candidate_returns[:168],row.peer_common_returns[:168]); second=half_cokurtosis(row.candidate_returns[168:],row.peer_common_returns[168:])
    if first is None or second is None:return None
    return {"decision_ms":row.decision_ms,"symbol":row.symbol,"first_value":first,"second_value":second,"minimum_value":min(first,second),"maximum_value":max(first,second),"path":tuple(f"{v:.12f}" for v in row.path_displacements)}

def evaluate_decision(rows:Sequence[CokurtosisCandidatePath])->dict|None:
    if len(rows)<10 or len({r.symbol for r in rows})!=len(rows) or len({r.decision_ms for r in rows})!=1:return None
    eligible=[v for v in (candidate_statistics(r) for r in rows) if v is not None]
    if not eligible:return None
    rank_count=ceil(len(rows)/4)
    first={v["symbol"] for v in sorted(eligible,key=lambda v:(-v["first_value"],v["symbol"]))[:rank_count]}
    second={v["symbol"] for v in sorted(eligible,key=lambda v:(-v["second_value"],v["symbol"]))[:rank_count]}
    admitted=[v for v in eligible if v["first_value"]>=1.50 and v["second_value"]>=1.50 and v["symbol"] in first and v["symbol"] in second]
    if not admitted:return None
    selected=sorted(admitted,key=lambda v:(-v["minimum_value"],-v["maximum_value"],v["symbol"]))[0]
    return {"decision_ms":selected["decision_ms"],"symbol":selected["symbol"],"minimum_half_cokurtosis":f"{selected['minimum_value']:.12f}","maximum_half_cokurtosis":f"{selected['maximum_value']:.12f}","path":selected["path"]}

def evaluate_stream(rows:Iterable[CokurtosisCandidatePath])->dict:
    input_rows=decision_groups=candidate_events=independent_episodes=0; digest=hashlib.sha256(); group=[]; current=None; previous=None
    def consume(values):
        nonlocal decision_groups,candidate_events,independent_episodes,previous
        if not values:return
        decision_groups+=1; event=evaluate_decision(values)
        if event is None:return
        candidate_events+=1; decision=int(event["decision_ms"])
        if previous is None or decision-previous>86_400_000:
            independent_episodes+=1; digest.update(json.dumps(event,sort_keys=True,separators=(",",":")).encode())
        previous=decision
    for row in rows:
        input_rows+=1
        if current is None:current=row.decision_ms
        if row.decision_ms!=current:consume(group);group=[];current=row.decision_ms
        group.append(row)
    consume(group)
    return {"input_rows":input_rows,"decision_groups":decision_groups,"candidate_events":candidate_events,"independent_episodes":independent_episodes,"event_digest":digest.hexdigest()}
