# Next Action

## Current Decision

M1G remains closed as `failed_validation`; its OOS was never opened. M1H has
now completed only its independent design package locally:

- Candidate identity: `FUNDING-EXTREME-SPOT-CONTRARIAN`; registered hash unchanged.
- Economic route: a settled extreme negative funding observation may represent crowded short positioning whose later unwind supports spot appreciation.
- Position and return source: spot long/cash and later spot-price movement only.
- Funding role: public crowding/sentiment information only; no funding cashflow.
- Timing: no use before `fundingTime`; any future entry must be strictly later than settlement.
- Data cadence: fundingInfo, then multiple premium schedules, then adjacent historical settlements; no fixed default interval.
- Non-duplication: no M1G spot-panic trigger and no M1B perpetual short, basis hedge, payback or funding-income rule.
- Execution: no exit selected; a later zero-mismatch representability review is mandatory before implementation.

This is a design-level pass, not evidence of events, frequency, displacement,
profitability or implementation feasibility.

## Immediate Sequence

1. Review and merge the M1H design-only package with all checks successful.
2. Keep M1H `declared_unopened`; no event, return or OOS has been read.
3. After merge, create a separate branch that freezes one M1H paper protocol before any IS event scan.
4. The future protocol must define the negative-funding extreme, interval-aware normalization, event clustering, post-settlement legality and frozen 120/30 plus 1.80% paper Gates.
5. The protocol PR must not run the event scan or select target, stop, holding period, position size or cooldown.
6. Only after that protocol merges may one sealed-IS paper-feasibility run be considered.
7. If M1H fails feasibility or any later Gate, stop BTC/ETH two-asset indicator research and require a new ADR for a broader liquid spot universe.

## Boundaries

- No strategy is eligible for M2.
- Do not enter M2.
- Freqtrade-first remains the architecture: Freqtrade owns future single-leg lifecycle and return evidence; Python may only audit timing, metrics and exported evidence.
- Do not create M1H strategy code, a backtest runner, performance audit or second strategy engine.
- Do not access OOS, private data, API keys, private smoke, dry-run/live, orders, cancellation, matching, wallets, trading permissions or `execution/live`.
- Do not commit raw, DuckDB, Freqtrade runtime data, logs, SQLite, `.env` or private payloads.

The M0 public dual-source audit remains a separate blocker. Before an M1H
paper run, funding lineage and per-event interval evidence must be explicitly
qualified without weakening that audit.
