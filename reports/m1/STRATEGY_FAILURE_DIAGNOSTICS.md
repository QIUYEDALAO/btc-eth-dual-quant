# Strategy Failure Diagnostics

- Status: diagnostics_complete_no_strategy_approved
- Generated UTC: 2026-07-09T23:30:00Z
- Scope: M1A and M1B failure diagnosis only
- Freqtrade role: primary framework for any future single-leg strategy research
- New backtest run: no
- Parameter tuning: no
- Gate reduction: no
- M2 approval: no
- Trading approval: no

## Evidence Validity

- M1A remains `failed_validation`.
- The historical M1A equal-weight alignment and delete-best-three numerical
  result are superseded. They are not used here as approval evidence.
- M1A symbol-level OOS Sharpe and low trade count independently preserve the
  failed decision.
- The M1B event-time revalidation report is the current numerical evidence.
- M0 infrastructure remains accepted, but its public dual-source audit remains
  blocked by official source differences and missing daily archives.

## M1A Trend Diagnosis

### Observed Evidence

- Data range: 2017-08-17 through 2026-07-08, approximately 8.89 years.
- Complete trades: 35 combined, approximately 3.94 trades per year.
- OOS trades: 7 over approximately 2.67 years, or 2.63 trades per year.
- BTC OOS Sharpe: 0.4861.
- ETH OOS Sharpe: 0.5698.
- Fixed neighborhood: 81 combinations.
- Neighborhood trade-count range: 29 to 44; required count: 80.
- Neighborhood full-sample Sharpe range: 0.5656 to 0.9452.
- No neighborhood point reaches either 80 trades or full-sample Sharpe 1.0.
  This is diagnostic breadth evidence, not an OOS gate rerun.
- Base and doubled-cost results remain positive, so modeled transaction cost is
  not the primary failure driver.

### Diagnosis

The fixed daily Donchian/SMA trend family is structurally too sparse for the
BTC/ETH-only universe under the unchanged validation gate. The neighborhood
does not show a single unlucky center parameter: every tested combination
remains far below 80 trades, and none reaches full-sample Sharpe 1.0. The
separate fixed-rule OOS evidence also remains below its gate.

The payoff profile is also strongly right-tailed: a small number of major bull
trends account for much of the historical result, while several bear or early
segments produce no trades. This makes the result dependent on rare regimes
and leaves only seven OOS trades. The exact historical delete-best-three
portfolio number is superseded, but the broader concentration risk remains a
valid diagnostic concern.

### M1A Decision

- Keep the self-managed M1A engine frozen.
- Do not choose a parameter from the neighborhood.
- Do not reduce the trade-count or OOS Sharpe gate.
- Do not port new features into the frozen M1A reproduction.
- Any future single-leg candidate must be a separately specified Freqtrade
  strategy hypothesis, not a parameter rescue of M1A.

## M1B Funding-Arbitrage Diagnosis

### Observed Evidence

- Current evidence range: 2020-01-01 through 2024-12-31.
- Complete cycles: 13; required: 20; shortfall: 7 cycles.
- Incomplete end positions: 2.
- Complete-cycle frequency: approximately 2.6 per year across BTC and ETH.
- Entry-year distribution: 2020 = 7, 2021 = 4, 2022 = 0, 2023 = 2,
  2024 = 0 complete entries.
- Mean complete-cycle holding period: 104.38 days.
- Median holding period: 86.33 days.
- Longest holding period: 267.67 days.
- Longest no-trade/sleep period: 713 days.
- OOS complete cycles: 2.
- Base cost, doubled cost, OOS Sharpe, and maximum-drawdown gates pass.

### Diagnosis

M1B fails because qualifying opportunities are scarce under the unchanged
26.0714% payback-required APR and strict exit rules. It does not fail because
of modeled cost or drawdown. Long holding periods and a 713-day sleep period
mean that five calendar years generate only 13 complete observations.

The high OOS Sharpe is supported by only two complete OOS cycles and therefore
does not compensate for the failed sample-size gate. Returns are economically
concentrated in a few unusually strong funding regimes, including two very
large cycles. This is consistent with a potentially useful but infrequent
market structure, not evidence ready for automation.

Extending the history without changing rules is the only valid way to test
whether sample scarcity improves. However, newer approval evidence must wait
until the relevant M0 public audit differences are resolved or explicitly
bounded by an approved data-authority decision.

### M1B Decision

- Keep `failed_validation`.
- Do not lower the 20-cycle gate or the payback threshold.
- Do not treat high Sharpe or positive cost-stress results as M2 approval.
- Keep the Python module as the single offline two-leg accounting sidecar.
- Do not represent two independent Freqtrade bots as a coordinated arbitrage
  system.
- Defer any external coordinator work to architecture design review only.

## Comparative Priority

| Track | Main failure | Evidence character | Decision |
| --- | --- | --- | --- |
| M1A trend | structurally sparse signals and weak OOS evidence | broad failure across the fixed neighborhood | freeze; do not rescue |
| M1B funding arbitrage | insufficient complete cycles | economically interesting but sample-limited | retain for offline research only |
| New Freqtrade single-leg candidate | not yet specified | no evidence yet | next design-review priority |

## Recommended Next Work

The next task should be a **Freqtrade single-leg strategy candidate design
review**. It must define a genuinely new, fixed hypothesis, its economic
rationale, data contract, OOS split, cost stress, minimum sample size, failure
criteria, and no-lookahead checks before strategy code is written.

M1B remains a secondary research track. It may be rerun on longer audited
public history without changing rules after the M0 data-authority blocker is
resolved. External two-leg coordinator work remains design-only.

## Gate

- M1A eligible for M2: no
- M1B eligible for M2: no
- Any strategy eligible for M2: no
- Freqtrade framework approved for research: yes
- Freqtrade strategy approved for automation: no
- Current status: diagnostics_complete_no_strategy_eligible_no_m2

## Prohibited Interpretation

This report does not approve live trading, paper trading with a real API,
`execution/live`, order placement, order cancellation, simulated matching,
API trading permissions, leverage expansion, or real-capital deployment.
