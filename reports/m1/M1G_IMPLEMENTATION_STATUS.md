# M1G Freqtrade Implementation Status

- Status: implementation_pass_no_performance_run
- Candidate: M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION
- Scope: exact Freqtrade strategy, causal fixtures, and conservative execution repricing audit
- Performance backtest executed: no
- Candidate return computed: no
- OOS opened: no
- API key used: no
- Live or dry-run used: no
- M2 authorized: no

## Fixed Implementation

- Signal authority: Freqtrade 2026.6, completed 1h bars.
- Execution detail: canonical 5m bars after entry only.
- Entry event: exact M1G-02 prior-only median protocol.
- Exit: +1.80% target, -4.00% stop, 24h timeout.
- Risk: 25% equity cap, one position, 72h all-pair cooldown.
- Gap handling: every discontinuity resets the 169-bar warmup.
- Pair selection: return multiple, then range multiple, then BTC exact-tie priority.
- Parameter search: none.

## Mandatory Audit

Python accepts only Freqtrade-exported trade lifecycles and canonical 5m OHLC.
It does not detect events or select trades. Same-5m ambiguity resolves to stop,
stop gaps use the worse open, target gaps use the exact target, and timeout uses
the first 5m open at or after 24 hours. Native and audited exit bars must match
before a future numerical result can pass.

## Validation

- Contract and configuration fixtures: pass.
- Prior-only and future-invariance fixtures: pass.
- Gap rewarm and connected-cluster fixtures: pass.
- Cross-pair ranking and exact-tie fixture: pass.
- Global all-pair cooldown fixture: pass.
- Conservative target/stop/gap/timeout repricing fixtures: pass.
- Pinned runtime lookahead-analysis: pass; 20 signals, zero biased entries/exits/indicators.
- Pinned runtime recursive-analysis: pass; startup 170/250/340, zero indicator variance and zero indicator lookahead.
- Runtime: official Freqtrade 2026.6 image pinned by digest.
- Runtime artifacts committed: no.

This implementation status does not approve a performance run, OOS access,
paper trading, live trading, order placement, execution/live, or M2.
