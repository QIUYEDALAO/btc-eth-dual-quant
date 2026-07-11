# Liquid Spot Universe Expansion Design

## Purpose

Replace exhausted BTC/ETH indicator mining with a survivorship-safe, point-in-time
research universe. This stage establishes membership and data eligibility only.

## Architecture

M0 discovers historical Binance spot USDT archives and emits one immutable monthly
membership snapshot. A snapshot uses only evidence completed before its effective
month. Freqtrade will later consume deterministic membership; it will not reconstruct
history from a current dynamic pairlist. No strategy or return calculation exists in
the universe builder.

## Contract

The versioned machine contract fixes Top 15, a prior-90-complete-day median daily
quote-volume rank, 365 complete history days, UTC-month activation, symbol tie-break,
and conservative stable/fiat/leveraged/wrapped exclusions. BTC and ETH are ordinary
eligible assets and additional regime/risk benchmarks.

## Qualification Flow

1. Discover historical USDT spot symbols from official public archives.
2. Merge monthly daily rows with fill-only daily supplements.
3. Evaluate point-in-time history, ranking-window and data-quality eligibility.
4. Rank eligible symbols and retain at most 15 for each month.
5. Qualify 5m archive coverage for selected members and derive 1h only from complete 5m buckets.
6. Write ignored detailed evidence plus a sanitized summary report.

Qualification failures remain visible; the builder never fills an unqualified slot
with an ineligible asset. No outcome, signal, event, PnL, Sharpe or OOS data is used.

## Acceptance

Tests must prove strict prior-window timing, deterministic ranking, exclusion,
delisting preservation, monthly-over-daily precedence, gap blocking, exact 5m-to-1h
aggregation and repeatable hashes. Safety scans must show no API key, private data,
strategy, order or execution implementation.
