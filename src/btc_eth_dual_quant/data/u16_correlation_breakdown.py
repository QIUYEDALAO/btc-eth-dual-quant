"""U-16 candidate evaluator shared by synthetic preflight and sealed Paper observation."""
from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from math import isfinite,sqrt
from typing import Iterable

@dataclass(frozen=True)
class CorrelationCandidatePath:
    decision_ms:int
    symbol:str
    candidate_returns:tuple[float,...]
    peer_common_returns:tuple[float,...]
    path_displacements:tuple[float,...]

def pearson(x:tuple[float,...],y:tuple[float,...])->float|None:
    if len(x)!=len(y) or len(x)<2:return None
    mx=sum(x)/len(x);my=sum(y)/len(y)
    dx=tuple(v-mx for v in x);dy=tuple(v-my for v in y)
    vx=sum(v*v for v in dx);vy=sum(v*v for v in dy)
    if vx<=0 or vy<=0:return None
    value=sum(a*b for a,b in zip(dx,dy))/sqrt(vx*vy)
    return value if isfinite(value) else None

def evaluate_candidate(row:CorrelationCandidatePath)->dict|None:
    if len(row.candidate_returns)!=48 or len(row.peer_common_returns)!=48 or len(row.path_displacements)!=6:return None
    if any(not isfinite(v) for v in (*row.candidate_returns,*row.peer_common_returns,*row.path_displacements)):return None
    recent_relative=tuple(a-b for a,b in zip(row.candidate_returns[36:],row.peer_common_returns[36:]));displacement=sum(recent_relative)
    if displacement<.024 or sum(v>0 for v in recent_relative)<7 or max(abs(v) for v in row.candidate_returns[36:])>.06:return None
    if max(recent_relative[-1],0)/displacement>.50:return None
    baseline=pearson(row.candidate_returns[:36],row.peer_common_returns[:36]);recent=pearson(row.candidate_returns[36:],row.peer_common_returns[36:])
    if baseline is None or recent is None or baseline<.50 or recent>.10 or baseline-recent<.50:return None
    return {"decision_ms":row.decision_ms,"symbol":row.symbol,"baseline_correlation":f"{baseline:.12f}","recent_correlation":f"{recent:.12f}","relative_displacement":f"{displacement:.12f}","path":tuple(f"{x:.12f}" for x in row.path_displacements)}

def evaluate_stream(rows:Iterable[CorrelationCandidatePath])->dict:
    count=events=0;digest=hashlib.sha256()
    for row in rows:
        count+=1;event=evaluate_candidate(row)
        if event is not None:
            events+=1;digest.update(json.dumps(event,sort_keys=True,separators=(",",":")).encode())
    return {"input_rows":count,"candidate_events":events,"event_digest":digest.hexdigest()}
