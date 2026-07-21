# U-09 Frozen-Source Data Qualification

- Status: `pass`
- Contract: `f1bd609d74210f6aa1b31f902d2dfecb79448bed4a0db8532a37be7321cead9a`
- Result: `c323798a9de04c423b8bb59c33604b2203715e1453f9b95b3f13022f71656aee`

All 27,736 frozen ZIP identities and CRCs, 19 audited V4 manifests, 78 monthly
memberships and 1,170 rank rows pass. The fixed schedule has 123 IS anchors
before the sealed boundary and 122 anchors with a complete non-overlapping 336h
primary horizon. Normal, reverse and deterministic-shuffled traversal are exact.

The qualification decoded zero OOS OHLC values and generated zero cohort,
event, path or return rows. It authorizes exactly one sealed-IS Paper
observation under the frozen protocol; no second run or parameter change is
authorized.

No strategy, backtest, API/trading, `execution/live` or M2 is authorized.
