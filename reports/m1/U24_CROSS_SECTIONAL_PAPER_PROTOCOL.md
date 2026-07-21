# U-24 Outcome-Blind Lottery-Demand Avoidance Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U24-03-LOTTERY-DEMAND-AVOIDANCE-PREMIUM-PAPER-V1`
- Protocol hash: `5110c3f455274f291391ed9b34affe6e5f61beb9198723d4fb0b8f07439c7ce7`
- Synthetic feasibility: `ce8b0f7998cc1c8e3928c605cccd0da37087a620d37e8058ae55e02f26957484`

Before any public-data or result access, the exact core passed three synthetic
million-row checks. The protocol fixes 336 completed 1h returns in two 168h
halves, candidate-specific peer-median common adjustment, each half's maximum
positive residual as the lottery payoff, an 8% ceiling and lowest-quartile
persistence in both halves. Decisions occur only at completed UTC 4h
boundaries and observations begin at the strict next expected 5m open.

Only a separate exact-head independent review is authorized. Data
qualification, returns, event/path scans, formal strategy returns, fixed rules,
Freqtrade code, backtesting, OOS, API/trading, `execution/live` and M2 remain
false.
