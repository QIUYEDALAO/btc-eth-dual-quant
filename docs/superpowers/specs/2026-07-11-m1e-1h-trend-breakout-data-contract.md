# M1E 1h Trend-Breakout Data Contract

- Design status: approved_data_contract
- Candidate: `M1E-1H-TREND-BREAKOUT`
- Candidate evaluated: no
- OOS opened: no
- Strategy code authorized: no

## Scope

This specification admits a new data-qualification trial, not a strategy. M1E
uses Binance BTC/USDT and ETH/USDT spot bars. A future signal may use only
completed UTC 1h bars, a future fill model may use 5m bars, and completed 4h
bars may be informative only. The direction is spot long or cash; shorting and
leverage are excluded.

The exact machine contract is `config/m1e_1h_data_contract.json`. Numeric
thresholds in that file are immutable caller-independent policy values.

## Trial Identity

The exact hypothesis is stored in `STRATEGY_TRIAL_LEDGER.yaml` with SHA-256
`3668032467e2f46edff7f0ab27d358d0b918889518bfaf97276699cbc783ed15`.
The trial remains `declared_unopened` and `oos_opened=false`. Registering it does
not increment an opened-trial count.

M1E is independently named and governed. A future design may not reproduce the
combined M1A fingerprint: SMA(200), Donchian 55 entry, Donchian 20 exit, and
ATR(20) 2x stop. No replacement indicators or thresholds are selected here.

## Data Authority

The qualification search starts at `2020-01-01` and ends at the last instant of
the latest complete UTC month.

1. Official monthly spot ZIP is authoritative for 5m, 1h, and 4h bars.
2. Official daily ZIP can add only absent timestamps. It cannot overwrite a
   monthly row.
3. Public REST is sampled evidence. It cannot enter or mutate golden data.
4. Twelve consecutive 5m bars deterministically produce one 1h bar.
5. Four consecutive 1h bars deterministically produce one 4h bar.
6. Missing children reject the aggregate. No fill, interpolation, or fake bar
   is permitted.

Derived and official OHLCV values must match numerically. Formatting-only
differences are evidence but do not block. Timestamp, ordering, or numeric
differences block qualification.

## Outage And Liquidity Rules

Qualification states are `audit_complete`,
`audit_complete_with_confirmed_outage`, and `blocked`.

A confirmed outage requires aligned evidence from both symbols across monthly
and daily ZIP availability and the 5m/1h time ranges. It remains an explicit
non-tradable gap. A one-symbol gap or source contradiction is blocked. Any
future rolling indicator that crosses an outage must remain unavailable until
its full lookback has rebuilt from consecutive bars.

For each symbol/month, the authoritative monthly 1m p95 spread proxy must be no
greater than 0.30%, equal to the fixed Cost x2 one-side budget. The caller
cannot override this value. Future result reports must retain Base 0.15%, Cost
x2 0.30%, Stress A 0.40%, and Stress B 0.55% per side.

## Admission Sequence

PR2 must locate the first six consecutive months where both symbols meet data
and liquidity qualification. The research start is the first day of the next
month. This selection cannot inspect signals, trades, equity, or returns.

Only if PR2 passes may PR3 compute the fixed 70/30 calendar split. It requires
at least 1800 complete historical days and at least 540 sealed-OOS days. A pass
authorizes only an IS-only trend-breakout feasibility design, not strategy code
or OOS access.

## Safety Boundary

This work performs no Freqtrade backtest and defines no entry, exit, position
size, or risk rule. It does not access API keys, private endpoints, private
smoke, paper/live trading, order operations, matching, or `execution/live`.
M2 remains blocked.
