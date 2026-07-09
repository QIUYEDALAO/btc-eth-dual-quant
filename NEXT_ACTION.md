# Next Action

Implement the approved Freqtrade-first hardening sequence:

1. Architecture governance and historical evidence notices: completed in PR #8.
2. Correct M0 funding-interval and ZIP/REST audit semantics: code hardening merged in PR #9; real audit evidence remains blocked and must not be treated as pass.
3. Pin and validate Freqtrade as the primary research framework: completed in PR #10.
4. Revalidate M1B with strict 1-hour event-time semantics: completed in PR #11; result remains `failed_validation`.

Immediate action: review `docs/superpowers/specs/2026-07-10-m0-dual-source-audit-unblock-design.md`. After explicit approval of the written specification, prepare a detailed implementation plan for the multi-network, evidence-first public audit. Do not begin implementation before that review gate. The audit must explain the spot ZIP/REST differences and obtain compliant official futures REST/ZIP evidence without private API access or region-bypass techniques.

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
