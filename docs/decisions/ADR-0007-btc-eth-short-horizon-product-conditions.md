# ADR-0007 BTC/ETH Short-Horizon Product Conditions

- Status: Accepted
- Date: 2026-07-10

## Context

M1A, M1B, and M1C failed validation. Independent expert review proved that the
project had consumed incompatible Sharpe and drawdown definitions, while the
correct daily-MTM recompute kept M1C failed. The prior daily panic-only proposal
also did not match the desired continuously evaluated short-horizon product.

## Decision

- Name the product the BTC/ETH 15m short-horizon event quant system, not intraday.
- Use Binance BTC/USDT and ETH/USDT spot only.
- Use completed 15m candles for signals, 1m as authoritative backtest detail,
  and 5m as sensitivity evidence.
- Restrict M1D to discrete large-dislocation events with a prior gross edge
  sufficient to cover the 0.60% Cost x2 round trip.
- Do not set a holding duration or daily trade quota; both are strategy outputs.
- Limit concurrent exposure to one position and prohibit shorting and leverage.
- Use daily-MTM D1-D6 metrics, PSR/DSR, a 15% MaxDD cap, and the fixed 25/25/50
  policy benchmark as decision Gates.
- Use one reversion target, one time expiry, and one hard-risk stop; prohibit
  multi-level ROI and OOS-driven tuning.
- Build one canonical 1m golden dataset, derive 5m/15m, quarantine official
  source conflicts, and require invariant Gate decisions across data variants.
- Require invariant Gate decisions across 15m, 5m-detail, and 1m-detail runs.
- Register every candidate hypothesis by exact text and SHA-256 before opening OOS.
- Keep M2, dry-run, live, API credentials, and order operations prohibited.

## Consequences

- Existing Freqtrade summary risk fields cannot be Gate inputs.
- Continuous small-move indicator families are outside the M1D product contract.
- Full minute-data runs occur locally or on the VPS; CI remains fixture-based.
- Most candidates are expected to fail; failure cannot lower thresholds.
- A future multi-strategy portfolio review may move benchmark comparison to the
  portfolio layer, but this single-strategy plan keeps it at strategy level.

## Evidence

- `reports/expert/2026-07-10-FABLE5-EXPERT-REVIEW.md`
- `reports/expert/m1c_recompute.py`
- `reports/expert/m1c_oos_daily_equity.csv`
- `docs/superpowers/specs/2026-07-10-btc-eth-short-horizon-event-quant-design.md`
