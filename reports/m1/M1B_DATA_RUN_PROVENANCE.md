# M1B Data Run Provenance

- generated_utc: 2026-07-09T17:20:20Z
- run_location: local
- data_source: Binance public data only
- transport: public REST attempted; official data.binance.vision ZIP fallback used because local REST TCP connections timed out
- metrics_methodology: funding-period time-indexed equity curve
- oos_methodology: time-based last 30%
- previous_cycle_level_metrics_superseded: yes
- superseded_reason: cycle-level equity curve distorted annualized volatility, Sharpe, and OOS Sharpe
- no API key used: yes
- no private data used: yes
- private smoke run: no
- raw data committed: no
- DuckDB committed: no
- logs committed: no
- private local report committed: no

## Data Windows

- spot_klines requested: BTCUSDT, ETHUSDT, 1d, 2017-08-17 through 2026-07-08
- futures/funding requested: BTCUSDT, ETHUSDT, 1d, 2019-09-01 through 2026-07-08
- report overlap used by M1B: 2020-01-01 through 2024-12-31
- overlap reason: local public spot monthly ZIP data available through 2024-12-31 while futures/funding ZIP data extends later

## Commands Summary

```bash
PYTHONPATH=src python3 scripts/m0_backfill_public.py \
  --symbols BTCUSDT,ETHUSDT \
  --interval 1d \
  --start-date 2017-08-17 \
  --end-date "$END_DATE" \
  --limit 1000 \
  --max-pages 20 \
  --spot-only \
  --zip-fallback \
  --timeout-sec 2 \
  --report-path reports/m0/M0_PUBLIC_SPOT_FULL_REPORT.local.md

PYTHONPATH=src python3 scripts/m0_backfill_public.py \
  --symbols BTCUSDT,ETHUSDT \
  --interval 1d \
  --start-date 2019-09-01 \
  --end-date "$END_DATE" \
  --limit 1000 \
  --max-pages 30 \
  --include-oi \
  --oi-period 1d \
  --zip-fallback \
  --timeout-sec 2 \
  --report-path reports/m0/M0_PUBLIC_FUTURES_FULL_REPORT.local.md

PYTHONPATH=src python3 scripts/m1b_run_funding_arbitrage_backtest.py
```

## Notes

- `reports/m0/*.local.md`, `storage/raw/`, and `storage/duckdb/` remain local-only artifacts.
- `openInterestHist` was not required by the M1B funding-arbitrage numerical report.
- Mark/index/premium datasets were used as diagnostics where continuous local data was available; missing or non-continuous diagnostics are recorded as `basis_data_unavailable` in the report.
- No live trading, paper trading with real API, execution/live, order placement, cancellation, simulated matching, private smoke, API key, secret, account balance, income amount, tranId, or raw private payload was used.
