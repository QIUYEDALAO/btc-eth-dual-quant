# Next Action

Implement the approved Freqtrade-first hardening sequence:

1. Architecture governance and historical evidence notices: completed in PR #8.
2. Correct M0 funding-interval and ZIP/REST audit semantics: code hardening merged in PR #9; real audit evidence remains blocked and must not be treated as pass.
3. Pin and validate Freqtrade as the primary research framework: completed in PR #10.
4. Revalidate M1B with strict 1-hour event-time semantics: completed in PR #11; result remains `failed_validation`.

P0 completed in merged PR #14. Immediate action: review, validate, and merge P1 PR #15 on `codex/m1c-btc-eth-rotation-design`. The fixed candidate is the BTC/ETH/cash weekly rotation on UTC daily candles. P1 has a `design_pass` based on the pinned Freqtrade source, but P2 strategy code is prohibited until PR #15 and CI pass.

After P1 merges, create `codex/m1c-btc-eth-rotation-validation` and execute P2. Its first hard Gate is the pinned-image fixture proving old-pair exit and new-pair entry share the same next-open timestamp. If that fixture fails, record `blocked_framework_capability`; do not create a second single-leg backtester. P3-P4 may proceed only after their predecessor Gate passes. P5-P8 remain `not_authorized`.

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
