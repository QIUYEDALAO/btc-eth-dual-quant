# Next Action

Implement the approved Freqtrade-first hardening sequence:

1. Architecture governance and historical evidence notices: completed in PR #8.
2. Correct M0 funding-interval and ZIP/REST audit semantics: code hardening merged in PR #9; real audit evidence remains blocked and must not be treated as pass.
3. Pin and validate Freqtrade as the primary research framework: completed in PR #10.
4. Revalidate M1B with strict 1-hour event-time semantics: completed in PR #11; result remains `failed_validation`.

Immediate action: review PR #13's completed proxy-assisted public audit evidence. The approved explicit loopback proxy resolved official futures REST connectivity and is disclosed as transport only; official Binance Vision ZIP retrieval remained direct. Official daily ZIP evidence recovered 936 rows omitted from selected monthly archives, but the strict gate still blocks on three source-level issues: historical spot revisions and one ZIP-only timestamp per symbol; BTCUSDT/ETHUSDT UM monthly and daily ZIP values that agree with each other but differ from REST at `2024-10-28T20:00Z` and `2024-10-28T21:00Z`; and REST-only mark/index/premium rows on `2026-06-29`, whose six required official daily ZIP URLs currently return HTTP 404. Future work may seek Binance source-owner clarification and recheck the missing daily archives after publication. It must not use third-party substitution, ZIP-only acceptance, or weaker comparison rules.

Rules:

- No strategy is eligible for M2.
- M0 remains accepted infrastructure but is audit_revalidation_required until step 2 passes.
- Historical M1A/M1B numerical claims marked superseded or invalidated must not support approval.
- The strict M1B event-time report is the current numerical evidence and remains failed_validation.
- Do not enter M2.
- Do not run live trading.
- Do not run paper trading with real API.
- Do not request, read, or use API keys.
- Do not implement execution/live.
- Do not place or cancel orders.
