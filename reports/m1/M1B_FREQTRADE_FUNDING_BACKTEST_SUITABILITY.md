# M1B Freqtrade Funding Backtest Suitability

- Scope: funding-rate-arbitrage backtest suitability review only.
- No live trading.
- No paper trading with real API.
- No execution/live.
- No order placement/cancel.
- No API trading permissions.
- No result approves live trading.

## Sources Reviewed

- Freqtrade Backtesting documentation: https://www.freqtrade.io/en/stable/backtesting/
- Freqtrade Leverage / futures documentation: https://www.freqtrade.io/en/stable/leverage/
- Freqtrade Exchange notes: https://www.freqtrade.io/en/stable/exchanges/
- Freqtrade Data download documentation: https://www.freqtrade.io/en/stable/data-download/
- Local Freqtrade Lab files under `freqtrade_lab/`.
- Local environment check on this machine.

## Suitability Questions

| Question | Finding |
| --- | --- |
| Freqtrade 是否支持 backtesting？ | Yes. Freqtrade has a native backtesting mode for strategy research. |
| Freqtrade 是否支持 Binance spot？ | Yes. The existing M1F Lab already uses Binance spot public data for research/backtest smoke checks. |
| Freqtrade 是否支持 Binance futures？ | Yes, in futures trading mode for supported futures exchanges including Binance futures-style markets. |
| Freqtrade 是否支持 futures short？ | Yes. Futures strategies can set `can_short = True` and emit short entry/exit signals. |
| Freqtrade spot 模式是否能 short？ | No. Shorting requires futures mode; spot mode is long-only in normal Freqtrade operation. |
| Freqtrade 是否能在一个策略中同时持有 spot long 和 futures short？ | No native evidence found. A strategy runs under one configured `trading_mode`; spot and futures are not managed as two coordinated legs inside one portfolio object. |
| Freqtrade 是否能在一次回测中同时处理两个 market type：spot 与 futures？ | Not as a native single combined spot+futures portfolio backtest. The configuration selects one `trading_mode`, and pair formats differ between spot and futures. |
| Freqtrade 是否能逐期计入真实 fundingRate？ | Partially. Freqtrade futures backtesting can use funding-rate data when available, and has a `futures_funding_rate` fallback setting for unavailable rates. |
| Freqtrade 是否能输出 funding income、basis PnL、spot leg PnL、perp leg PnL 的独立拆分？ | Not natively for a two-leg arbitrage portfolio. A futures-only backtest can reflect funding fees, but it does not produce full arbitrage accounting decomposition across spot and perpetual legs. |
| Freqtrade 是否能控制两腿净敞口 <= 5%？ | Not natively without an external coordinator, because one bot/strategy cannot observe and reconcile a separate spot leg against a futures leg in the same backtest portfolio. |
| Freqtrade 是否能表达单腿成交失败、对齐失败、保证金不足等套利事故？ | Not for a native spot-long plus futures-short pair. These are cross-leg coordination failures and need an external arbitrage coordinator or custom offline simulator. |
| Freqtrade futures funding data 缺失时会如何处理？ | It requires funding-rate data for futures backtests where funding fees matter; when unavailable, docs describe a `futures_funding_rate` fallback. |
| 如果设置 futures_funding_rate = 0 或其他常量，是否会导致资金费套利回测失真？ | Yes. A constant fallback can be acceptable for isolated futures strategy smoke tests, but it materially distorts funding-rate-arbitrage validation because funding income is the core return source. |

## Minimal Experiment Status

- Added config: `freqtrade_lab/user_data/configs/config.futures-funding-backtest.example.json`.
- Added probe strategy: `freqtrade_lab/user_data/strategies/M1BFuturesFundingProbeStrategy.py`.
- Purpose: verify futures backtesting, short signal support, public futures data download, and whether funding fees appear in Freqtrade output.
- Experiment run status: not_run in this local environment.
- Reason: local Docker CLI is unavailable and `VPS_HOST` is not set in this shell, so the official Freqtrade Docker image could not be executed safely here.
- No API key was requested, read, or used.
- No private smoke was run.
- No live or paper command was run.

Suggested public-data-only experiment commands for a prepared lab host:

```bash
docker compose -f freqtrade_lab/docker-compose.yml run --rm freqtrade download-data \
  --userdir /freqtrade/user_data \
  --config /freqtrade/user_data/configs/config.futures-funding-backtest.example.json \
  --trading-mode futures \
  --timeframes 1d \
  --pairs BTC/USDT:USDT ETH/USDT:USDT \
  --timerange 20240101-20240301

docker compose -f freqtrade_lab/docker-compose.yml run --rm freqtrade backtesting \
  --userdir /freqtrade/user_data \
  --config /freqtrade/user_data/configs/config.futures-funding-backtest.example.json \
  --strategy M1BFuturesFundingProbeStrategy \
  --timerange 20240101-20240301
```

These commands are research-only. They must not be converted to `freqtrade trade`, must not use exchange credentials, and must not be used as live or paper trading approval.

## Why Two Bots Are Not Enough

- A two-bot setup would introduce leg sync risk.
- A two-bot setup would introduce reconciliation risk.
- A futures bot cannot reliably know the spot bot's true fills, position size, slippage, or failed orders.
- Single-leg exposure, margin, net exposure, basis PnL, and funding PnL reconciliation require an external coordinator or custom accounting layer.
- Running one spot bot and one futures bot can be a lab experiment, but it is not a native arbitrage backtest that proves spot-long plus perpetual-short behavior.

## Conclusion

Conclusion: **B. Freqtrade 可承担部分功能，但需要外部组合/对账/资金费回测器。**

Freqtrade remains useful for:

- single-leg spot research;
- single-leg spot trend research;
- futures short strategy smoke tests;
- parts of futures backtesting;
- futures-only public-data backtesting;
- UI and research workflow exploration.

Freqtrade is not sufficient by itself for M1B final validation of spot-long plus USDT perpetual-short funding-rate arbitrage because the strategy requires cross-market portfolio accounting, leg synchronization, funding-income decomposition, basis PnL decomposition, and net-exposure controls that are outside a native single Freqtrade strategy/backtest run.

Freqtrade can support futures short probes, but those probes do not natively prove a coordinated spot-long plus perpetual-short funding-arbitrage portfolio. A two-bot setup is not accepted as native arbitrage support because it leaves leg synchronization, reconciliation, single-leg exposure, basis accounting, and funding accounting outside Freqtrade.

External coordinator/accounting remains required for M1B funding-rate-arbitrage research validation.

## Decision Impact

- Do not merge PR #5 as a completed custom M1B numerical validation.
- Do not proceed to M2.
- Keep custom offline funding-arbitrage backtester only as a research/accounting candidate unless a future Freqtrade experiment proves native support.
- If future Freqtrade futures experiments expose adequate funding-fee detail, use Freqtrade for the futures leg smoke and keep external portfolio reconciliation for the arbitrage portfolio.
- Do not treat Freqtrade as a direct funding-arbitrage execution engine.
- No live trading, paper trading with real API, order placement, API key use, or M2 approval is implied.
