# M1G Fixed Rule Contract

- Status: frozen_pre_implementation
- Candidate: M1G-1H-PANIC-DISLOCATION-MEAN-REVERSION
- Contract: M1G-04-FIXED-RULE-V1
- Parameter search used: no
- Alternative rules evaluated: no
- Freqtrade strategy implemented: no
- Backtest executed: no
- OOS opened: no
- M2 authorized: no

## Entry

- Use the exact merged M1G-02 price-only panic-event protocol.
- Decide only after the completed event 1h candle closes.
- Earliest fill is the next available 5m open; same-1h-close fill is forbidden.
- If BTC and ETH qualify for the same decision time, rank by absolute-return
  multiple, then true-range multiple, then BTC for an exact tie.
- No 4h or volume filter is used.

## Exit

- Profit target: +1.80% from actual entry price.
- Invalidation stop: -4.00% from actual entry price.
- Maximum holding time: 24 hours.
- Evaluate target and stop with post-entry 5m detail.
- If both touch in one 5m candle, record the stop first.
- A stop gap fills at the worse of the stop threshold or that 5m open.
- A target gap receives only the target threshold.
- Timeout fills at the first 5m open at or after 24 hours.
- No trailing stop and no ROI table.

## Risk

- At most one BTC/ETH position at a time.
- Position cap: 25% of current account equity.
- Global cooldown: 72 hours after every exit.
- No leverage, short, position adjustment, averaging down, martingale or grid.
- A 4.00% stop on a 25% position implies 1.00% planned equity risk before
  fees, slippage and stop gaps. Actual loss can be worse and must be measured.

## Derivation

The +1.80% target is the preregistered paper hurdle, three times the 0.60% Cost
x2 roundtrip. The stop rounds the observed -3.31% median 24h MAE outward to
-4.00%; combined with the 25% cap it gives a 1% planned equity loss at the stop.
The 24h timeout matches the frozen paper horizon. The 72h global cooldown limits
repeated exposure to observed event clusters, which reached seven events in a
rolling week.

These are single deterministic choices, not a search space. The contract does
not assume capture of the observed 2.69% median MFE and does not hide the
-21.58% worst paper MAE.

## Next Gate

After this contract is reviewed and merged, a Freqtrade implementation may be
considered in a separate task. Implementation must reproduce this contract
exactly and pass time-semantics, lookahead and recursive checks before any IS
backtest. OOS, M2, dry-run, live and trading permissions remain prohibited.
