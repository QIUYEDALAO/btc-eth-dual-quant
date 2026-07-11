# M1G IS Validation Protocol

- Status: frozen_before_is_result
- Protocol: M1G-08-IS-VALIDATION-V1
- Candidate return accessed: no
- IS performance run executed: no
- OOS opened: no
- Trial count: 3
- M2 authorized: no

## Frozen Run

- IS: `2020-07-01T00:00:00Z` to `2024-09-11T00:00:00Z`, end exclusive.
- Signal/detail: completed 1h / canonical 5m.
- Pairs: BTC/USDT and ETH/USDT spot.
- Runtime: Freqtrade 2026.6 pinned by digest.
- Costs per side: Base 0.15%, Cost x2 0.30%, Stress A 0.40%, Stress B 0.55%.
- Stress A/B are mandatory diagnostics and have no post-result hard threshold.
- Python may reprice exported trades only; it may not detect or select signals.

## Frozen IS Gates

- Complete trades: at least 56.
- Base and Cost x2 total return: strictly positive.
- Daily-MTM Sharpe: at least 1.0.
- Daily-MTM PSR: at least 0.95.
- Daily-MTM maximum drawdown: at most 15%.
- Delete-best-three return: at least zero.
- Four contiguous segments: at least three positive.
- Strategy Sharpe not below the fixed risk-matched benchmark.
- Strategy drawdown not worse than the benchmark.
- Strategy total return strictly above the benchmark.
- Lookahead and recursive checks pass.
- Unexplained data gaps: zero.
- Native Freqtrade and conservative execution-audit results both pass.

Every strategy, configuration, audit, runtime and data-authority input is frozen
by SHA256 in the machine protocol. Any Gate failure stops M1G without opening
OOS or changing a parameter.
