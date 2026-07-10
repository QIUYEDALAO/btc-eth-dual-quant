# Next Action

Under the Freqtrade-first architecture, T1 merged in PR #21. Start T2 on a new
branch:

1. Produce golden 1m rows without overwriting monthly ZIP evidence.
2. Keep official conflicts in a separate quarantine table and preserve both variants.
3. Derive deterministic 5m/15m only from golden 1m after `2023-10-01`.
4. Compare derived 15m rows with official 15m ZIP evidence and export ignored Freqtrade caches.
5. Do not write M1D strategy code.

After T0, execute `T1 -> T2 -> T3 -> T4` before M1D feasibility. T5 must
pass before T6 fixed design, and T6 must pass before any Freqtrade strategy code.

Locked conditions: discrete completed-15m events, authoritative 1m detail, 5m
sensitivity, `max_open_trades=1`, no fixed holding duration, no daily trade
quota, daily-MTM MaxDD <=15%, OOS Sharpe >=1.0, and PSR >=0.95.

M1C remains `failed_validation` after expert correction. Its OOS daily-MTM
Sharpe is 0.7882/0.7528 and MaxDD is 23.47%/24.47%; do not tune or rescue it.

M0 source differences must be quarantined and sensitivity-tested. Never select
the more profitable official data version.

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
