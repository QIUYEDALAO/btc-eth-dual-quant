# U-23 Cross-Sectional Paper-Protocol Exact-Head Review

- Verdict: `approve`
- Target: `1d0b21282b1e499fdef0d9cab88e7a918a5d5913`
- Protocol hash: `52807bd0e2c0bd2276c88e1d919a7e4a375c480f51fe479f0934d8c0063e5611`
- Critical/high findings: `0/0`
- Review hash: `f2a8a5fdf770419bcc6f29abda3539d251b9e6e0f1dc97d5a4e824ab4f37c4a4`

The exact target uses every point-in-time active member's 42 prior plus one
current completed UTC 4h OHLC bars. It builds an own-history median and robust
MAD range baseline, then requires a material current range, 2x expansion and
three-scale robust deviation.

The same completed bar must close in its top 10%, contain a positive body over
60% of its range and exceed the complete active-peer median return by 2.5%.
The deterministic representative and 24h clustering are causal. Membership,
lifecycle and invalid-interval masks precede construction; future defects only
right-censor paths.

All 16 dimensions pass, including the exact pre-freeze 3/3 synthetic evidence
and core blob. Approval authorizes only frozen-source structural qualification
and result-free preflight. It does not authorize OHLC/result scanning, events,
paths, formal returns, strategy, OOS or trading.
