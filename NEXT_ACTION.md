# Next Action

Implement the approved Freqtrade-first hardening sequence:

1. Architecture governance and historical evidence notices: completed in PR #8.
2. Correct M0 funding-interval and ZIP/REST audit semantics: in progress on `codex/m0-audit-correctness-hardening`.
3. Pin and validate Freqtrade as the primary research framework.
4. Revalidate M1B with strict 1-hour event-time semantics.

Immediate action: review and merge the M0 correctness code as a truthful hardening artifact while keeping M0 `audit_revalidation_required`. Re-run the manual no-secret `M0 Public Audit` only from a compliant network that can access futures REST, and investigate the recorded spot ZIP/REST differences; do not restore audit pass until every required check passes.

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
