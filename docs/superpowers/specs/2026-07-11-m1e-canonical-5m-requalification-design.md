# M1E Canonical 5m Requalification Design

## Scope

Requalify the existing public M1E archive without changing append-only raw responses. This work resolves the system's source-authority ambiguity; it does not evaluate a candidate or calculate returns.

## Data Flow

1. Read monthly and available daily official 5m ZIP rows from the existing append-only run.
2. Use the existing public REST conflict evidence to identify daily revisions independently confirmed by REST.
3. Produce canonical 5m rows with a decision record for every fill or revision.
4. Derive 1h and 4h bars only from complete canonical child windows.
5. Compare derived bars with official higher-timeframe archives and classify differences as exact, format-only, flow revision, timestamp revision, or price revision.
6. Export ignored canonical data and quarantine evidence, then write a sanitized report.

## Blocking Rules

- Block: unresolved monthly/daily 5m conflict, invalid canonical 5m row, unexplained single-symbol gap, incomplete child window outside a confirmed common outage, or missing trace hashes.
- Quarantine without blocking: higher-timeframe flow revisions and higher-timeframe archive revisions when the complete canonical 5m chain remains valid.
- A future strategy using non-OHLC fields is outside this contract.

## Acceptance

The requalification passes only when both symbols have a traceable canonical 5m price series from the qualified start, deterministic 1h/4h derivation, zero unresolved canonical conflicts, and readable Freqtrade cache. Passing authorizes only the metadata sample-budget Gate.

No API key, private endpoint, strategy, backtest, OOS return, order, paper/live mode, or execution module is permitted.
