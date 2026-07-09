# Strategy Failure Diagnostics Design

## Status

- Design status: approved and implemented
- Phase: post-hardening strategy diagnostics
- Scope: evidence review only
- Strategy approval: none
- M2 approval: none

## Objective

Explain why the fixed M1A trend rule and fixed M1B funding-arbitrage rule
failed validation, without tuning either strategy, weakening a gate, or
creating execution behavior. The output must identify which findings are
structural, which are data-limited, and which historical metrics are no longer
valid for approval.

## Evidence Inputs

- `reports/m1/M1A_TREND_BACKTEST_REPORT.md`
- `reports/m1/M1A_REVIEW_DECISION.md`
- `reports/m1/M1A_REVALIDATION_NOTICE.md`
- `reports/m1/M1B_EVENT_TIME_REVALIDATION_REPORT.md`
- `reports/m1/M1B_FINAL_DECISION.md`
- `reports/m0/M0_AUDIT_REVALIDATION_REPORT.md`
- ADR-0005 and ADR-0006

No raw data, private data, API credentials, network access, or new backtest run
is required.

## Evidence Rules

1. The M1A `failed_validation` decision remains active.
2. M1A equal-weight alignment and delete-best-three numerical claims are
   superseded and may be cited only as historical artifacts, not approval
   evidence.
3. The strict M1B event-time revalidation report is the current M1B numerical
   evidence.
4. Positive returns, high Sharpe, or low drawdown cannot override an unchanged
   failed gate.
5. M0 audit differences remain an independent blocker for extending evidence
   into affected periods.

## Diagnostic Questions

### M1A

- Is failure caused by modeled cost, or by signal frequency and return
  concentration?
- Does the fixed parameter neighborhood show a local parameter accident or a
  broad structural pattern?
- Is the OOS evidence sufficiently strong for approval?

### M1B

- Is failure caused by cost, drawdown, event-time semantics, or complete-cycle
  scarcity?
- How are complete cycles distributed through time?
- Is the OOS Sharpe supported by enough independent complete cycles?
- Can extending the public history be used before the M0 audit blocker is
  resolved?

## Decision Framework

The diagnostic report may recommend only one of these research directions:

1. freeze a failed strategy;
2. perform a new strategy-hypothesis design review in Freqtrade;
3. extend evidence without changing rules after its data authority is valid;
4. perform architecture design review without execution.

It may not select a best parameter set, alter thresholds, approve M2, or
implement paper/live trading.

## Output

Generate `reports/m1/STRATEGY_FAILURE_DIAGNOSTICS.md` with:

- evidence-validity boundaries;
- M1A and M1B failure diagnosis;
- comparative priority;
- an explicit no-M2 decision;
- the next permitted design-review task.

## Validation

- Project context validation passes.
- Existing M0/M1A/M1B/M1F validation passes.
- Secret and no-trading scans remain clean.
- No raw, DuckDB, log, Freqtrade runtime, or private report artifact is tracked.
