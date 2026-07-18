# U-08 Frozen-Source Data Qualification

- Status: `pass`
- Contract: `0adc8d4928e245e05a981f6ad997be01cd1fea876c0717e6a8d85ee8ca31f51e`
- Result: `1ec26ef74b80c2b46cfd0dcb231ee8863ae2bd0ff01fabf33dd4028b13807cb5`
- Protocol target/review: `a516efb3...9361` / `316fe577...8acf`

All 27,736 frozen ZIP identities and CRCs, all 19 V4 manifests, 78 monthly
memberships and 1,170 exact rank rows pass. Every month has unique ranks 1–15,
unique symbols, positive finite prior-only liquidity values and ranking/history
windows ending at membership effectiveness.

Normal, reverse and deterministic-shuffled traversal share
`ca7d59b3...44aa`. OOS OHLC decoded, membership-entry events, paths and returns
are all zero. This pass authorizes exactly one sealed-IS Paper observation; no
strategy, backtest, OOS, trading or M2.
