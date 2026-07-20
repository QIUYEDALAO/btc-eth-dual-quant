# ADR-0016: Existing-Strategy Adaptation Route

- Status: pre-runtime contract complete pending exact-head review
- Date: 2026-07-21

## Decision

The project stops the serial U-25/U-26+ from-scratch hypothesis route and uses
a fixed, source-pinned inventory of public Freqtrade strategies. U-25 is
superseded append-only; its original authorization record is not edited.

The repository is GPL-3.0-only. Every upstream source is bound to a commit,
source blob, file hash, archive hash, repository license, file-level license
decision and dependency closure. Unverified source 20 is metadata-only and is
not redistributed. Bandtastic retains its file-level MIT declaration.
All 20 entries are screened in their preregistered order. The first six passing
entries are frozen; exactly five are acceptable if only five pass. Fewer than
five is a hard stop.

Compatibility work may change interfaces, equivalent indicator calls,
next-open timing and fail-closed data guards only. It may not change economic
conditions, periods, thresholds, timeframe, ROI, stoploss, pair selection or
position logic. Original and adapter remain separate and hash-bound.

The unified IS contract freezes the exact data authority, 100,000 USDT fixed-
notional portfolio, next-eligible-5m execution model, four costs, two prior-only
active-universe benchmarks, hard Gates and deterministic selection order. Its
canonical hash is recorded in the machine ADR. The data authority binds the
existing V4 19/19 audited artifact set without decoding OOS values. The
benchmark extends the existing T3 daily-MTM/metrics module and has only
synthetic coverage; no candidate result is present.
The risk-matched benchmark is derived from a separately generated fixed-50%-
gross shadow curve: each Monday gross uses only the prior 90 complete candidate
returns and prior 90 shadow returns, never the risk-matched curve's own history,
and emits a weekly gross audit trace. Daily MTM supports at most five concurrent
different pairs, rejects same-pair overlap and is invariant to trade input order.
Membership and lifecycle exits occur at the current UTC-day open before any
Monday rebalance; an exited symbol requires that open but not a same-day close,
and its exit cost is charged exactly once.

The result-blind calendar uses source warmup `2020-01-01` through `2020-07-01`
and evaluates `[2020-07-01, 2026-07-01)`: 2,191 full days, 1,533 IS days and
658 sealed-OOS days (`30.0319488818%`). The completed-candle authority derives
15m/1h/4h only from exactly 3/12/48 eligible 5m rows, with no partial window,
fill, lifecycle crossing or invalid-interval-mask crossing. Execution may use
only the strict next eligible 5m open and may not search forward.
Daily equity uses half-open return labeling: the anchor observation is
`2020-06-30`, the first return is labeled `2020-07-01`, and the final return is
`2026-06-30`. Full/IS/OOS return counts are exactly 2,191/1,533/658 and the
candidate plus both benchmarks must use identical labels.
The inventory no longer declares an overlapping evaluated-IS interval. It
binds this protocol as the sole calendar authority, while the data authority,
calendar day counts and equity labels are independently cross-checked. Every
IS trade must open at or after `2020-07-01T00:00:00Z` and close strictly before
`2024-09-11T00:00:00Z`; warmup, anchor-day, OOS-boundary and boundary-crossing
trades fail closed.

Trial manifests bind candidate, source, adapter, runtime, protocol, data,
benchmark and DSR identities plus every result file's path, kind, scenario,
byte hash and semantic hash. Cross-trial file reuse and path traversal fail
closed. DSR separately freezes the authoritative M1A/M1B/M1C Base and CostX2
Sharpe sequences; each future original or modified materialization appends once
per scenario while all four cost scenarios remain a single selection trial.
The historical inputs are explicitly heterogeneous and deliberately
conservative; no homogeneous trial-distribution claim is made. Their frozen
expected maximum Sharpes are 3.146768898019 (Base) and 3.001365569591 (CostX2).
Metrics are not trusted as standalone declarations. The checker converts the
hash-bound equity evidence to the shared `EquityPoint` form and calls
`metrics_from_equity` to reconcile net return, daily-MTM Sharpe, PSR and maximum
drawdown within `1e-10`; completed-trade count is reconciled to the trades
evidence. Base/CostX2 DSR is then recomputed from daily returns and the complete
historical-plus-selection sequence. StressA/B never enter that sequence.
Each candidate may have at most one original and one modified manifest, no more
than three candidates may be modified, and modified trials require a unique
preregistered package plus a materialized, reconciled passing original whose
timestamp is strictly earlier. Original executable identity equals the frozen
base adapter; a modified executable equals the package `after_hash`. Package
identity covers its id, before/after hashes and one or two atomic changes.
Base/CostX2 Sharpes are derived only from reconciled hash-bound equity evidence
ordered by materialization UTC and trial ID.
Original or modified IS results, when eventually authorized by successful
causal validation, increment `selection_trial_count` on first materialization;
DSR uses `3 + selection_trial_count` and cost scenarios do not add trials. A
maximum of one preregistered modification
package per candidate and two atomic changes per package is allowed. At most
one candidate may be selected. OOS is single-use and remains separately sealed.

All contracts are bound by `config/adr0016_pre_runtime_contract_freeze_v1.json`.
The checker hard-codes that root file's byte hash, so coordinated edits to the
ADR and child hashes cannot silently re-authorize work.

## Current stop boundary

The route remains blocked by four independent prerequisites: PR #112 exact-head
review/merge, verification of the pinned VPS runtime identity, freezing runtime
effective parameters, and successful causal validation for at least five
candidates. The route stops before runtime load and all performance results.

No IS may start until AST-declared parameters have been resolved by the pinned
runtime and each frozen candidate has a non-null
`runtime_effective_settings_hash` and `runtime_resolved_parameters_hash`, and
observed external parameter/config override counts of zero. Required counts are
pre-registered at zero; observed values remain null until the future VPS load.

## Prohibitions

OOS, dry-run, API keys, private endpoints, paper/live trading, order placement,
`execution/live` and M2 remain false.
