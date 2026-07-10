# M1E 1h Product And Data Contract

- Status: design_contract_pass
- Candidate: M1E-1H-TREND-BREAKOUT
- Candidate evaluated: no
- OOS opened: no
- Trial count incremented: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

## Locked Contract

| Item | Value |
| --- | --- |
| Market | Binance spot BTC/USDT, ETH/USDT |
| Direction | long/cash only; no leverage |
| Signal authority | completed UTC 1h |
| Execution detail | 5m |
| Regime input | completed 4h only |
| Qualification range | 2020-01-01 through latest complete UTC month |
| Source order | monthly ZIP; daily ZIP fill-only; REST compare-only |
| Liquidity Gate | monthly 1m p95 spread proxy <= 0.30% |
| Common qualification | first six consecutive BTC/ETH months |
| Research start | following month first day |
| Full/OOS minimum | 1800 / 540 days, OOS sealed |

M1E may not reuse the combined M1A SMA200, Donchian 55/20, ATR20 2x rule
bundle. No replacement strategy rule has been chosen. Data qualification is the
only next authorized operation.

M1A, M1B, M1C, and M1D statuses are unchanged. No report in this stage approves
trading.
