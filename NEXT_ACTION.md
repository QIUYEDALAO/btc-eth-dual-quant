# Next Action

Implement the approved Freqtrade-first hardening sequence:

1. Architecture governance and historical evidence notices: completed in PR #8.
2. Correct M0 funding-interval and ZIP/REST audit semantics: code hardening merged in PR #9; real audit evidence remains blocked and must not be treated as pass.
3. Pin and validate Freqtrade as the primary research framework: completed in PR #10.
4. Revalidate M1B with strict 1-hour event-time semantics: completed in PR #11; result remains `failed_validation`.

Immediate action: the multi-network, evidence-first audit implementation is complete, but its real gate remains blocked. Local and approved remote nodes both read official futures ZIP data but could not reach official futures REST. Exact spot comparison found synchronized BTCUSDT/ETHUSDT source revisions at `2020-12-21T13:00Z` and `2021-04-23T01:00Z`, plus a ZIP-only `2020-12-21T14:00Z` row for each symbol. Future work may seek official source-owner clarification or use another compliant network for official futures REST; it must not use a proxy/VPN bypass, third-party substitution, ZIP-only acceptance, or weaker comparison rules.

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
