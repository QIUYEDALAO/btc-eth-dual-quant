#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any,Mapping
ROOT=Path(__file__).resolve().parents[1];PROTOCOL=ROOT/"config/u14_cross_sectional_paper_protocol_v1.json";REPORT=ROOT/"reports/m1/U14_CROSS_SECTIONAL_PAPER_PROTOCOL.md";DESIGN=ROOT/"config/u14_cross_sectional_design_scope_v1.json";EXPECTED_HASH="a0b606d3996f0edd13790178f370bed92e3a6d06bf2298eea78ba8a46907ac57"
def canonical_hash(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def validate(d:Mapping[str,Any],report:str)->list[str]:
    f=[];identity={k:v for k,v in d.items() if k not in {"content_hash","generated_utc"}}
    if d.get("content_hash")!=EXPECTED_HASH or canonical_hash(identity)!=EXPECTED_HASH:f.append("protocol identity changed")
    if d.get("candidate_id")!="U14-CROSS-SECTIONAL-DOWNSIDE-REJECTION-PERSISTENCE" or d.get("design_content_hash")!="a6c3cc47c3cadf33e5673e59ce47c639d6df1d49c57f88c51cc1c8579b446691":f.append("candidate/design binding changed")
    auction=d.get("completed_auction_contract",{});selling=d.get("common_selling_pressure",{});event=d.get("event_identity",{})
    if auction.get("decision_time")!="each_completed_utc_4h_boundary" or auction.get("close_location")!="close_minus_low_divided_by_high_minus_low" or auction.get("all_active_member_48_five_minute_rows_complete_required") is not True:f.append("auction identity changed")
    if selling.get("common_component_maximum")!="-0.0060" or "times_7" not in selling.get("negative_breadth_integer_gate",""):f.append("selling state changed")
    expected_event={"candidate_completed_close_to_open_log_return_maximum":"0.0000","candidate_normalized_range_minimum":"0.0180","candidate_downside_excursion_maximum":"-0.0120","candidate_close_location_minimum":"0.80","candidate_close_location_residual_minimum":"0.20","representatives_per_decision_time":1,"absolute_positive_return_candidate_prohibited":True,"post_outcome_candidate_selection":False}
    if any(event.get(k)!=v for k,v in expected_event.items()):f.append("event identity changed")
    if d.get("episode_clustering",{}).get("connected_window_hours")!=24 or d.get("pre_result_sample_ceiling",{}).get("minimum_theoretical_eligible_24h_episodes")!=400:f.append("cluster or ceiling changed")
    bench=d.get("pre_result_complexity_benchmark",{})
    if bench.get("synthetic_fixture_rows")!=1000000 or bench.get("maximum_elapsed_seconds")!=30 or bench.get("maximum_peak_rss_mib")!=1024 or bench.get("benchmark_passes_required")!=3 or bench.get("required_before_unique_result_run") is not True:f.append("complexity benchmark changed")
    pre=d.get("implementation_data_scope_preflight",{})
    if pre.get("oos_ohlcv_values_decoded")!=0 or pre.get("common_component_event_path_or_return_rows_generated")!=0 or pre.get("required_before_any_common_state_event_or_path_scan") is not True:f.append("preflight changed")
    gates=d.get("paper_gates",{})
    if gates.get("complete_is_independent_episodes_minimum")!=90 or gates.get("combined_median_24h_relative_rejection_persistence_minimum")!="0.0180" or gates.get("fraction_complete_episodes_with_positive_24h_relative_rejection_persistence_minimum")!="0.60":f.append("Paper Gates changed")
    expected={"paper_protocol_frozen":True,"exact_head_independent_review":True,"data_qualification_complexity_and_preflight":False,"common_state_scan":False,"event_scan":False,"path_observation":False,"signals":False,"formal_returns":False,"fixed_rule_contract":False,"freqtrade_strategy_code":False,"backtesting":False,"oos":False,"api_trading":False,"execution_live":False,"m2":False}
    if d.get("authorizations")!=expected:f.append("authorization matrix changed")
    if EXPECTED_HASH not in report or "frozen_before_result_pending_exact_head_review" not in report:f.append("report identity changed")
    return f
def main()->int:
    d=json.loads(PROTOCOL.read_text());f=validate(d,REPORT.read_text())
    if json.loads(DESIGN.read_text()).get("content_hash")!=d.get("design_content_hash"):f.append("design drift")
    if f:print("u14_cross_sectional_paper_protocol_check FAIL");[print(f"- {x}") for x in f];return 1
    print(f"u14_cross_sectional_paper_protocol_check PASS hash={EXPECTED_HASH}");return 0
if __name__=="__main__":raise SystemExit(main())
