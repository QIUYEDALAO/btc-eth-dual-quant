# U-14 Downside-Rejection Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol hash: `a0b606d3996f0edd13790178f370bed92e3a6d06bf2298eea78ba8a46907ac57`
- Candidate: `U14-CROSS-SECTIONAL-DOWNSIDE-REJECTION-PERSISTENCE`

The protocol freezes completed UTC 4h auctions derived from exact 5m rows. A
decision requires a median close/open log return no greater than `-0.60%` and
at least 70% negative active members. The sole representative must itself have
non-positive return, at least `1.80%` range, at least `1.20%` downside excursion,
close-location at least `0.80`, and close-location residual at least `0.20`
versus event-time peers. This preserves auction rejection rather than U-07
positive-return relative strength.

Episodes cluster over connected 24h windows. Paths use the next expected 5m
open and fixed peers through 24h. Sample, distribution, `1.80%` relative and
absolute displacement, 60% sign and zero-mismatch Gates are immutable.

Before any unique result run, qualification must pass exact frozen-source
preflight and three passes of a one-million-row synthetic complexity benchmark
within 30 seconds and 1024 MiB. The benchmark and preflight produce no market
outcome rows and decode no OOS OHLCV values.

Only exact-head independent review is authorized. Data/results, formal returns,
strategy/backtesting, OOS, API/trading, `execution/live` and M2 remain false.
