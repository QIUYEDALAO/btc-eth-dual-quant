# M1F Freqtrade Funding Arbitrage Gap Analysis

Generated UTC: 2026-07-09T00:00:00Z

## Direct Questions

- Does Freqtrade support Binance futures? yes, as a framework capability, subject to exchange/mode support and configuration.
- Does Freqtrade support short? yes in futures mode where supported.
- Can Freqtrade spot mode short? no.
- Can one Freqtrade bot simultaneously manage spot long and USDT-margined perpetual short legs? unknown / not covered by this M1F deployment.
- If two bots are used, one spot and one futures, does that add reconciliation risk? yes. It can violate a single-coordinator assumption and introduces leg-sync, margin, exposure, and accounting risks.
- Can Freqtrade backtests reliably use historical funding rates? partially_covered / under_review. This must be verified with complete historical funding-rate inputs.
- If funding rates are incomplete, will backtest accuracy suffer? yes.

## Funding-Arbitrage Requirement Coverage

| Requirement | Freqtrade Native Coverage | Note |
|---|---|---|
| Spot long + perpetual short | partially_covered | Spot and futures capabilities exist, but coordinated two-leg arbitrage is not proven in one bot. |
| Net exposure <= 5% | not_covered | Requires external portfolio-level exposure reconciliation. |
| Real funding each period | partially_covered | Depends on historical funding-rate availability and backtest support. |
| Basis PnL included | partially_covered | Price data can model basis, but strategy/reporting must explicitly reconcile both legs. |
| Single-leg exposure control | partially_covered | Per-bot protections exist, but cross-leg exposure needs coordination. |
| Margin risk control | partially_covered | Futures mode has leverage/margin concepts, but arbitrage-specific margin stress controls need review. |
| Exchange incident risk controls | not_covered | Needs external kill-switch and incident workflow design. |
| Leg synchronization | not_covered | Requires an external arbitrage coordinator if not proven natively. |
| Reconciliation across spot/futures accounts | not_covered | Requires external accounting and monitoring. |

## Assessment

Freqtrade is suitable to evaluate as a framework for spot long-only strategy hosting and for possible single-leg futures research. It is not yet proven suitable as a native two-leg funding-arbitrage engine.

## Conclusion

B. Partial support, needs an external arbitrage coordinator.

Do not proceed to live trading, paper trading with real API credentials, or M2. The next approved work, if requested separately, should be a funding-rate-arbitrage backtest validation that explicitly models two legs, funding income, basis PnL, leg exposure, and reconciliation risk.
