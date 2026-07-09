# Next Action

Implement the approved Freqtrade-first hardening sequence:

1. Architecture governance and historical evidence notices: completed in PR #8.
2. Correct M0 funding-interval and ZIP/REST audit semantics: code hardening merged in PR #9; real audit evidence remains blocked and must not be treated as pass.
3. Pin and validate Freqtrade as the primary research framework: in progress on `codex/freqtrade-primary-framework-hardening`.
4. Revalidate M1B with strict 1-hour event-time semantics.

Immediate action: review the pinned Freqtrade primary-framework implementation, sanitized runtime manifest, VPS public smoke, and M0/Freqtrade data provenance. M0 remains `audit_revalidation_required`, and no framework smoke or provenance pass may approve M2.

Rules:

- No strategy is eligible for M2.
- M0 remains accepted infrastructure but is audit_revalidation_required until step 2 passes.
- Historical M1A/M1B numerical claims marked superseded or invalidated must not support approval.
- Do not enter M2.
- Do not run live trading.
- Do not run paper trading with real API.
- Do not request, read, or use API keys.
- Do not implement execution/live.
- Do not place or cancel orders.
