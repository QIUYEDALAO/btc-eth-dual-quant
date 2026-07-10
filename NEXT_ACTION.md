# Next Action

Implement the approved Freqtrade-first hardening sequence:

1. Architecture governance and historical evidence notices: completed in PR #8.
2. Correct M0 funding-interval and ZIP/REST audit semantics: code hardening merged in PR #9; real audit evidence remains blocked and must not be treated as pass.
3. Pin and validate Freqtrade as the primary research framework: completed in PR #10.
4. Revalidate M1B with strict 1-hour event-time semantics: completed in PR #11; result remains `failed_validation`.

P0 completed in PR #14, P1 design_pass in PR #15, and P2 implementation in PR #16. P2 static validation and pinned Freqtrade runtime run 29059474678 passed. Immediate action: run immutable P3 full-history validation on `codex/m1c-btc-eth-rotation-backtest`.

P3 must evaluate base and cost-x2 full/OOS returns, complete trade counts, OOS Sharpe, maximum drawdown, delete-best-three concentration, four fixed IS segments, lookahead, recursive analysis, and unexplained daily gaps. Any failure becomes `failed_validation` and stops this candidate without parameter rescue. P4 may run only if all P3 gates pass. P5-P8 remain `not_authorized`.

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
