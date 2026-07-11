# M1E IS Paper-Feasibility Protocol

- Status: frozen_before_result
- Protocol: M1E-06-COMPRESSION-EXPANSION-PAPER-V1
- Scope: IS-only event diagnostics
- Formal strategy return permitted: no
- OOS opened: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

## Event Definition

The diagnostic event is fixed before reading its outcomes:

1. On completed 1h bars, compute the prior 24-bar normalized high-low range.
2. Compare that completed compression score with the 20th percentile of the
   preceding 4,320 compression scores, excluding the current score.
3. The next completed bar is an expansion candidate only when its close exceeds
   the preceding 24-bar high and its true range is at least twice the median
   true range of those preceding 24 bars.
4. Require at least 4,345 consecutive bars in the current isolated segment.
5. Group same-symbol candidates connected within 24 hours and retain the first
   event as the diagnostic representative.

This is a diagnostic event family, not an entry rule. No 4h filter, volume,
position, fill, exit, stop, cooldown or portfolio model is used.

## Observations

- Reference price: completed event-bar close.
- Fixed horizons: 1, 2, 4, 8, 12 and 24 completed 1h bars.
- Path diagnostics: 24-hour MAE and MFE.
- Right-censored events are disclosed but excluded from Gate statistics.
- Costs are reference hurdles only: 0.30%, 0.60%, 0.80% and 1.10% roundtrip.
- No cost-adjusted trade return or equity curve is produced.

## Frozen Paper Gates

- Projected full events at least 120.
- Projected sealed-OOS events at least 30, using only IS event rate and calendar length.
- Combined median 24-hour MFE at least 1.80%.
- Each symbol has at least 20 complete events and median 24-hour MFE at least 1.80%.
- At least three calendar years contain at least ten events.
- No single year contains more than 45% of complete events.
- No Gate event may occur in quarantine or before complete segment warmup.

Any failure records `failed_feasibility`, closes M1E before strategy code, and
moves the queue to M1G. Thresholds may not be changed after this protocol commit.
