# M1C Freqtrade Capability Review

- Status: design_pass
- Scope: BTC/ETH/cash rotation design capability only
- Freqtrade release: 2026.6
- Source commit: `b604e2fd70539f7f73d3c62c16ce0b155bbab319`
- M2 approved: no
- Dry-run/live approved: no

## Capability Matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| BTC and ETH informative data | Freqtrade DataProvider supports cached historical pair/timeframe data | supported |
| One deterministic winner | Both aligned score columns are present on each pair; only the winner emits entry | supported by design |
| Sunday close to Monday open | Backtesting shifts all signal columns one candle | supported |
| One open position | `max_open_trades = 1` | supported |
| Keep at least 50% cash | `stake_amount = unlimited` with `tradable_balance_ratio = 0.5` | supported |
| Same-open rotation | Open-trade pair is processed first; closing decrements the slot before the new pair is processed | supported by pinned source |
| Runtime confirmation | P2 pinned-image fixture must compare old close and new open timestamps | required before implementation pass |

## Same-Open Ordering Evidence

At tag `2026.6`, `Backtesting._time_pair_generator_det()` prepends pairs with
open trades. `Backtesting.backtest_loop()` processes the existing pair and its
exit order. `LocalTrade.close_bt_trade()` decrements
`bt_open_open_trade_count` immediately. When the selected new pair is processed
later at the same timestamp, `trade_slot_available()` can accept it.

This is sufficient for P1 design acceptance. P2 must run the behavior through
the pinned Freqtrade image. A one-day delayed replacement, ambiguous pair
ordering, or inability to reproduce the fixture changes the status to
`blocked_framework_capability`; no custom single-leg backtester may replace it.

## Safety

This review created no strategy implementation, API configuration, dry-run,
live command, order operation, or execution module. It authorizes P2 research
implementation only after this P1 PR passes review.
