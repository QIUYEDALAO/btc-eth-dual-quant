"""Result-blind U-15 Paper evaluator shared by synthetic preflight and the later sealed run."""
from __future__ import annotations
from dataclasses import dataclass
from math import isfinite,log
from statistics import median
from typing import Iterable

@dataclass(frozen=True)
class TakerAuctionPathRow:
    decision_ms:int;symbol:str;open:float;close:float;quote_volume:float;taker_buy_quote_volume:float;reference_open:float;path_closes:tuple[float,...]

def evaluate_decision(rows:list[TakerAuctionPathRow])->dict|None:
    if len(rows)<10 or len({r.symbol for r in rows})!=len(rows) or len({r.decision_ms for r in rows})!=1:return None
    if any(not all(isfinite(x) and x>0 for x in (r.open,r.close,r.quote_volume,r.reference_open,*r.path_closes)) or not isfinite(r.taker_buy_quote_volume) or r.taker_buy_quote_volume<0 or r.taker_buy_quote_volume>r.quote_volume for r in rows):return None
    returns=[log(r.close/r.open) for r in rows];shares=[r.taker_buy_quote_volume/r.quote_volume for r in rows]
    center=median(shares);mad=median(abs(x-center) for x in shares);scale=1.4826*mad
    if not isfinite(scale) or scale<=0:return None
    common=median(returns);candidates=[]
    for row,ret,share in zip(rows,returns,shares):
        z=(share-center)/scale;relative=ret-common
        if share>=.60 and z>=2 and -.004<=relative<=0 and abs(ret)<=.006:candidates.append((z,share,-relative,row.symbol,row))
    if not candidates:return None
    chosen=max(candidates,key=lambda x:(x[0],x[1],x[2],tuple(-ord(c) for c in x[3])))
    row=chosen[-1];displacements=tuple(close/row.reference_open-1 for close in row.path_closes)
    return {"decision_ms":row.decision_ms,"symbol":row.symbol,"taker_buy_share":f"{chosen[1]:.12f}","taker_buy_share_z":f"{chosen[0]:.12f}","path":tuple(f"{x:.12f}" for x in displacements)}

def evaluate_stream(rows:Iterable[TakerAuctionPathRow],expected_members:int=15)->dict:
    current=None;group=[];events=[];count=0
    for row in rows:
        count+=1
        if current is None:current=row.decision_ms
        if row.decision_ms!=current:
            event=evaluate_decision(group) if len(group)==expected_members else None
            if event:events.append(event)
            group=[];current=row.decision_ms
        group.append(row)
    if group:
        event=evaluate_decision(group) if len(group)==expected_members else None
        if event:events.append(event)
    return {"input_rows":count,"candidate_events":len(events),"events":events}
