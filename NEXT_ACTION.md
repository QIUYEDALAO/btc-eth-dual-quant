# Next Action

## Current Decision

M1G remains closed as `failed_validation`. M1H remains `declared_unopened`,
and its pre-outcome paper protocol merged in PR #63 at `dd4ae5b`:

- Event identity: settled negative funding at or below the same-symbol prior-365-day lower 5% tail, with per-event interval annualization.
- Timing: settlement first, then the exact next expected canonical 5m open strictly after `fundingTime`.
- Observation: fixed 1/2/4/8/12/24-hour market-reaction windows only.
- Paper Gate: median 24h close displacement, not MFE alone; MFE/MAE/recovery remain mandatory path diagnostics.
- Non-duplication: no spot panic trigger and no funding carry, basis, hedge, perpetual short or two-leg logic.
- Leakage: event identity, windows, clustering and interval policy cannot change from results without a new ADR.

No historical event, event count, path result, return or OOS value has been read.

## Immediate Sequence

1. Start M1H-03 on a new branch; it is authorized but not yet executed.
2. Run pure funding-data qualification before loading any candidate event outcome.
3. Qualification may inspect only lineage, timestamps, per-event intervals, settlement availability, missing/duplicates, timezone and completeness.
4. If qualification fails, stop without event scanning or feasibility analysis.
5. If qualification passes, the same task may proceed once to sealed-IS paper feasibility without another intermediate approval.
6. Any frozen Gate failure closes M1H without tuning; failure stops BTC/ETH two-asset indicator research and requires a new ADR for a broader liquid spot universe.

## Boundaries

- No strategy is eligible for M2.
- Do not enter M2.
- Freqtrade-first remains the architecture: Freqtrade owns future single-leg lifecycle and return evidence; Python may only audit timing, metrics and exported evidence.
- Do not create M1H strategy code, a backtest runner, performance audit or second strategy engine. M1H-03 may implement only the frozen IS paper-observation runner after qualification passes.
- Do not access OOS, private data, API keys, private smoke, dry-run/live, orders, cancellation, matching, wallets, trading permissions or `execution/live`.
- Do not commit raw, DuckDB, Freqtrade runtime data, logs, SQLite, `.env` or private payloads.

The M0 public dual-source audit remains a separate blocker. The future M1H-03
qualification step must fail closed on funding lineage or interval defects and
must not weaken that audit.
