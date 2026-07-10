# M1E Canonical 5m Requalification Report

- Status: pass
- Contract: M1E data contract v2 / ADR-0009
- Scope: public-data requalification only
- Range: 2020-01-01 through 2026-06-30T23:59:59.999000+00:00
- Research start: 2020-07-01
- Canonical 5m REST-confirmed daily revisions: 12
- Unresolved canonical 5m conflicts: 0
- Canonical incomplete child buckets: 0
- Confirmed-outage child buckets isolated: 146
- Manifest SHA256: `3c8b080dbad2b53dfbb770dd5d92ad8104da1fa21b45b4b901e8ccffbea86793`

## Canonical Datasets

| Symbol | Timeframe | Rows | SHA256 |
| --- | --- | ---: | --- |
| BTCUSDT | 5m | 630719 | `f71b245fb06db63a8e1d69dad760dd0ca0079369b65314ab500c85377bfd9a01` |
| BTCUSDT | 1h | 52555 | `c7aba17e257e5182a04a728e61ca143fcbaeabf01c8fa83d0358e2e8930ecf9c` |
| BTCUSDT | 4h | 13129 | `6ae18296ecf27b8e649fce443da5d3cd2008055971ee68701b156e147501af57` |
| ETHUSDT | 5m | 630719 | `2533876832a77d5b7b76f83aa7aa6956f93895da6a29ca526776af5441f2d448` |
| ETHUSDT | 1h | 52555 | `223bf73fdf9fc5443cd9018651220cb2dfeb5890d496615023b2a1e0ac04502c` |
| ETHUSDT | 4h | 13129 | `c5fd00fe310bca7235848886059335161704caaa19828aa9728cbf5c11970cf9` |

## Audit-Only Higher-Timeframe Evidence

- audit_flow_revision_quarantined: 7
- audit_price_revision_quarantined: 2
- audit_timestamp_revision_quarantined: 40
- exact: 263
- Higher-timeframe audit differences do not replace canonical 5m-derived OHLC.
- Flow-field revisions are quarantined and are not admissible for a future volume-based strategy.

## Gate

- Canonical 5m traceable: pass
- Unresolved canonical price conflicts zero: pass
- Deterministic 1h/4h derivation: pass
- Freqtrade list-data: pass
- Metadata-only sample-budget stage authorized: yes
- Candidate evaluated: no
- OOS prices/returns accessed: no
- Strategy code authorized: no
- Freqtrade backtesting run: no
- API key used: no
- Private data used: no
- M2 authorized: no

## Historical Evidence

ADR-0008 and the original blocked qualification report remain unchanged. This report supersedes only their admission decision under the explicitly revised source-authority contract.
