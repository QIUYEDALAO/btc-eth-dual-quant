# ADR-0009: M1E Canonical 5m Data Authority

- Status: accepted for data requalification only
- Date: 2026-07-11

## Context

ADR-0008 treated monthly 5m, official 1h/4h archives, daily archives, and current REST as if they were immutable copies of one historical database. Binance public history contains documented revisions: lower-timeframe OHLC can be confirmed by daily ZIP plus REST while monthly ZIP remains unchanged, and higher-timeframe flow fields can differ even when OHLC agrees. Requiring every official representation to match made the audit wait indefinitely for a source-owner response although the price series could be reconstructed deterministically.

## Decision

M1E contract version 2 uses official 5m bars as the only canonical price layer. Monthly 5m ZIP is the base. Daily 5m ZIP fills missing rows and may replace a conflicting monthly row only when public REST independently confirms the daily row. The replacement is a derived canonical decision: neither append-only source is modified, and both hashes and the decision reason are retained.

Canonical 1h bars are derived from exactly twelve consecutive canonical 5m bars. Canonical 4h bars are derived from exactly four consecutive canonical 1h bars. Official 1h/4h ZIP and REST rows are audit comparators only.

An unresolved conflict in canonical 5m OHLC, an invalid bar, or an unexplained single-symbol gap blocks admission. A higher-timeframe flow-field revision is quarantined and reported but does not block a price-only M1E study. M1E decision fields are limited to OHLC. Any future use of volume, quote volume, trade count, or taker volume requires a new data contract and requalification.

## Consequences

- Old ADR-0008 reports remain immutable historical evidence.
- A new requalification report decides whether the revised data Gate passes.
- Binance issue responses remain useful evidence but are no longer an operational dependency.
- This ADR does not authorize strategy rules, OOS access, Freqtrade backtesting, M2, API credentials, or trading.
