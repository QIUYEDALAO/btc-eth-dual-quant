# Next Action

Implement the approved Freqtrade-first hardening sequence:

1. Architecture governance and historical evidence notices: completed in PR #8.
2. Correct M0 funding-interval and ZIP/REST audit semantics: code hardening merged in PR #9; real audit evidence remains blocked and must not be treated as pass.
3. Pin and validate Freqtrade as the primary research framework: completed in PR #10.
4. Revalidate M1B with strict 1-hour event-time semantics: completed in PR #11; result remains `failed_validation`.

P0 completed in PR #14, P1 design_pass in PR #15, P2 implementation in PR #16, and M1C P3 failed-validation evidence in PR #17. The candidate is closed. There is no active implementation task and P4 is blocked.

M1C failed complete-trade count (31 < 80), OOS complete-trade count (15 < 20), OOS Sharpe (0.1146 < 1.0), and maximum drawdown (16.65% > 15%). Do not tune or rescue it. P4 is blocked because P3 did not pass. Any future work requires a separately approved new P1 candidate design or M0 audit diagnostics. P5-P8 remain `not_authorized`.

M0 monitoring continues independently. PR #13 merged as truthful blocked evidence: official futures REST connectivity is complete, but historical spot/UM source differences and missing `2026-06-29` daily reference-price archives keep audit revalidation blocked. Do not weaken the data gate to accelerate strategy work.

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
- Follow `PROJECT_EXECUTION_CHECKLIST.md` in dependency order.
