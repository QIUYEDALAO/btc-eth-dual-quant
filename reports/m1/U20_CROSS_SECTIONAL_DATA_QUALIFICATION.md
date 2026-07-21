# U-20 Frozen-Source Data Qualification and Preflight

- Status: `pass_local_complete`
- Contract hash: `7bae7234c15f6f378b5b28667d3e805e51a34465bd95c736b0a3ef2109f49f80`
- Qualification hash: `de61add6f8ef2a22f62166c14aeb4c30565cb8b3003e6395909fa7b7a85e2368`
- Protocol target: `6a2207c05c7045e82b47f9685c01a5c2d0b30755`

All 27,736 frozen archives and 19 V4 manifests remain exact. Normal, reverse
and deterministic-shuffled source traversal agree; the same-reader structural
preflight also agrees in all three orders. It finds 5,179 eligible structural
decisions and a maximum of 752 independent theoretical 24h episodes, passing
the frozen minimum ceiling of 400.

The exact future U-20 evaluator processed one million synthetic candidate rows
three times in 26.868, 27.130 and 27.207 seconds, with identical output hash
`59beecf0...ade4` and peak RSS 26.250 MiB. All passes satisfy the 30-second and
1,024-MiB Gates.

Qualification decoded zero price, return, common-adjusted-return, coskewness,
candidate, event, path, formal-return or OOS result rows. It used no network and
mutated no frozen evidence. Exactly one sealed-IS Paper observation is now
authorized; strategy, backtesting, OOS, trading and M2 remain prohibited.
