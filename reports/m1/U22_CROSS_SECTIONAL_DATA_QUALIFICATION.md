# U-22 Frozen-Source Data Qualification

- Status: `pass_local_complete`
- Contract hash: `59cf9567c06b73418404202063407f716056c80d584993b2b50a4b5b75482875`
- Result hash: `9b009c6b940e338cc77f8f3ea9e8dd473689c739d6c247ad0ba078c3f40a2334`

All 27,736 frozen archives and 19 manifests are exact. Normal, reverse and
deterministic-shuffled source and same-reader traversals agree. The 24h-history
plus 24h-path structural preflight yields 37,401 eligible decisions and a
maximum 1,514 independent 24h episodes versus 400 required.

The pre-freeze synthetic core evidence remains exact and was not rerun. This
stage decoded zero price/return/dispersion/leader/event/path or OOS values.
Exactly one sealed-IS Paper observation is authorized; strategy, backtesting,
OOS and trading remain false.
