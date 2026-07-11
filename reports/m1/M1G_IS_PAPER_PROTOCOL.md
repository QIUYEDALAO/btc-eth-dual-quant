# M1G IS Paper Protocol

- Status: frozen_before_result
- Protocol: M1G-02-PANIC-DISLOCATION-PAPER-V1
- Scope: protocol definition only
- Event scan executed: no
- Candidate outcomes accessed: no
- Formal strategy returns permitted: no
- OOS opened: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

## Frozen Event Definition

On completed UTC 1h OHLC only, a paper event must satisfy all conditions:

1. Close-to-close return is at most `-2.40%`.
2. Its absolute return is at least `3.0` times the median absolute return of the
   prior 168 completed bars, excluding the event bar.
3. Its true range is at least `2.5` times the median true range of the prior 168
   completed bars, excluding the event bar.
4. Its close location is in the bottom 25% of its own high-low range.
5. At least 169 bars exist in the current continuous segment.
6. Same-symbol events connected within 24 hours form one cluster; retain only
   the first event.

The 2.40% absolute displacement is four times the frozen 0.60% Cost x2
roundtrip. The relative-return, range-expansion and close-location conditions
encode urgent one-sided liquidity without using volume or future information.
No 4h filter or volume field is used.

## Frozen Observations

- Reference price: completed event-bar close; this is path evidence, not a fill.
- Horizons: 1, 2, 4, 8, 12 and 24 completed 1h bars.
- Path window: 24 hours for MAE/MFE.
- Right-censored events are disclosed and excluded from Gate statistics.
- Full/OOS event counts are projected only from complete IS cluster representatives.
- Tail diagnostics include median and maximum MAE, P05 24h displacement, and
  rolling 24h/7d event clustering.
- No entry, exit, position, cost-adjusted return or equity curve is produced.

## Frozen Paper Gates

- Projected full events at least 120.
- Projected sealed-OOS events at least 30.
- Combined median 24h MFE at least 1.80%.
- Each symbol has at least 20 complete events and median 24h MFE at least 1.80%.
- At least three years contain at least ten events.
- No single year contains more than 45% of complete events.
- No Gate event occurs in quarantine or before complete segment warmup.

Any failure closes M1G as `failed_feasibility` before strategy code and moves
the frozen queue to M1H. The protocol cannot be changed after outcome access.

## Authorization

This record freezes the protocol only. After it is merged, a separate task may
run the protocol once on sealed IS snapshots. This record does not itself
authorize that run, fixed rules, Freqtrade backtesting, OOS or M2.
