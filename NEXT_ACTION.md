# Next Action

## Immediate Task

Complete U-04 frozen-source data qualification and IS/OOS isolation.

- Reviewed target: `6523b83d6b6ba93771ec1bad15625eb191fa07be`.
- Protocol hash: `7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6`.
- Review hash: `34fe2efdf4788b20b915f34b3b6442f60ddaa364103ae90b920dc2cacf9646b1`.
- Review verdict: `approve`; critical/high: `0 / 0`.
- Source freeze: `c86310f8...ec6c`; artifact set: `8784b564...348c3`.

Verify exact frozen ZIP/source identity, canonical 5m validity, mask-before-grid,
complete 1h construction, point-in-time active membership, lifecycle
end-exclusive semantics and the fixed IS/OOS boundary. Normal, reverse and
deterministic-shuffled traversal must produce the same qualification identity.

This is a data-only task. It must not compute member returns, median/MAD,
residuals, candidate counts, episodes, paths or performance. It must reject
timestamps at or after `2024-09-11T00:00:00Z` from any IS research reader and
must not expose sealed-OOS OHLC values.

Passing qualification may authorize exactly one sealed-IS paper observation.

## ADR-0015 Implementation Exact-Head Review

Historical review marker: exact implementation review remains `approve` with
zero critical/high findings under review hash `9a073643...e5af1`.

## ADR-0015 Independent Policy Review

Historical review marker: policy review remains `approve` under review hash
`893d056e...85a3`; U-04 data work does not change policy semantics.

## U-03F Repair Exact-Head Review

Historical review marker: the former repair review and its later blocked cold
run remain immutable. ADR-0015 requalification separately quarantined 119 physical
invalid rows plus the valid-minority slot.

## Prohibited

- No strategy is eligible for M2. Do not enter M2.
- Freqtrade-first remains mandatory for future single-leg implementation.
- Do not scan U-04 events, observe paths, calculate returns or inspect OOS.
- Do not change the reviewed protocol, thresholds, Gates or authorities.
- Do not implement strategy/fixed-rule/backtest logic.
- No API keys, dry-run/live trading, `execution/live` or order operations.
- Local Git only; no push, PR or GitHub Actions.
