# ADR-0011: Expand The Point-in-Time Liquid Spot Universe

- Status: accepted_for_data_qualification_only
- Date: 2026-07-12

## Context

M1E, M1G and M1H exhausted the frozen BTC/ETH candidate queue without opening
M1G or M1H OOS. Adding another BTC/ETH indicator would be indicator mining.
The next research question is whether cross-asset response differences exist in
a historically reconstructable liquid spot universe.

Freqtrade remains the only future strategy and return engine. Its current-market
dynamic pairlists are not historical membership evidence, so M0 must construct
point-in-time membership before Freqtrade research begins.

## Decision

For each UTC calendar month, rank eligible Binance spot USDT pairs by the median
daily quote volume over the 90 complete UTC days ending before that month. Select
at most 15 pairs, descending by the metric and then ascending by symbol. The
membership becomes effective at 00:00 UTC on the first day of the month.

Eligibility requires 365 complete historical UTC days, a complete 90-day ranking
window, official archive evidence, conflict-free OHLCV, no unexplained symbol-only
gap, and future 5m research-data availability. Stable-value or fiat-pegged assets,
leveraged tokens, and wrapped or pegged duplicates are excluded by the versioned
machine contract. Fewer than 15 qualified assets is valid and must be disclosed.

Historical delisted assets remain eligible during months in which the evidence
available at that time qualified them. Current `exchangeInfo` and current market
rankings may not rewrite historical membership. BTC and ETH follow the same
eligibility rules and may enter the universe; they additionally remain market
regime and risk benchmarks.

## Data Authority

- Official monthly daily ZIP is primary for ranking and historical availability.
- Official daily ZIP fills missing timestamps only and never overwrites monthly rows.
- Public REST is sampled evidence only and never overwrites ZIP authority.
- Official 5m archives qualify future execution-detail availability.
- Complete 5m rows may deterministically derive 1h evidence; interpolation is forbidden.
- Runtime raw data, detailed manifests, DuckDB and Freqtrade caches remain ignored.

## Consequences

M0 owns monthly point-in-time manifests. Freqtrade may later consume deterministic
membership slices, but no strategy family is selected by this ADR. Python must not
become a second cross-sectional return engine.

This ADR authorizes only asset and data qualification. It does not authorize event
scanning, signals, returns, OOS access, Freqtrade backtesting, M2, API credentials,
orders, dry-run or live trading. Any change to 15 assets, 90 days, 365 days, the
ranking metric, tie-breaker, exclusion policy or activation timing requires a new ADR.
