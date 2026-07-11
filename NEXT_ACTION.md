# Next Action

## Current Decision

M1G completed its one permitted frozen IS run after protocol PR #58 merged.
The result is `failed_validation`:

- Base: 179 trades, native return -22.6272%, conservative return -21.3551%.
- Cost x2: 177 trades, native return -28.3540%, conservative return -31.5286%.
- Base daily-MTM Sharpe/PSR/MaxDD: -1.3195 / 0.0013 / 23.9747%.
- Cost x2 daily-MTM Sharpe/PSR/MaxDD: -1.6457 / 0.0001 / 29.5509%.
- Every one of the four contiguous IS segments lost money under Base and Cost x2.
- Conservative repricing found 66 Base and 83 Cost x2 exit-bar mismatches, so the mandatory execution-audit Gate also failed.

The paper-feasibility pass did not translate into positive expectancy. This is
the intended purpose of the staged process: reject an attractive event envelope
before spending the sealed OOS.

## Immediate Sequence

1. Review and merge `reports/m1/M1G_IS_VALIDATION_REPORT.md` with all CI checks successful.
2. Keep M1G OOS sealed and keep the DSR opened-trial count at three.
3. Do not tune the -2.40% event, +1.80% target, -4.00% stop, 24h timeout, 25% cap or 72h cooldown.
4. After the M1G failure record merges, the only next candidate work is a separate M1H funding-extreme spot-contrarian design review.
5. M1H must remain spot long/cash; funding is a public sentiment signal only, not a futures leg or two-leg execution design.
6. If M1H fails its independent chain, stop BTC/ETH two-asset indicator mining and require a new ADR before considering a broader liquid spot universe.

## Boundaries

- No strategy is eligible for M2.
- Do not enter M2.
- Freqtrade-first remains the architecture: Freqtrade owns single-leg strategy lifecycle and return evidence; Python only audits time, metrics and exported-trade repricing.
- Do not open M1G OOS or increment its trial count.
- Do not run private smoke or read/request API keys.
- Do not run dry-run/live or implement orders, cancellation, matching, wallets, trading permissions or `execution/live`.
- Do not commit raw, DuckDB, Freqtrade runtime data, logs, SQLite, `.env` or private payloads.

The M0 public dual-source audit remains a separate evidence blocker and may be
investigated without private API access. It does not change the M1G failure.
