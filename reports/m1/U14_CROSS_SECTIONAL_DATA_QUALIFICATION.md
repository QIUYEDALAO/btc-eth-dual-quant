# U-14 Cross-Sectional Data Qualification, Complexity Benchmark and Preflight

- Status: `pass_local_complete`
- Contract hash: `bea82ceabcab8ff22f8c5e0d8beab636886ab42e776bfe93be382e0719b45951`
- Qualification hash: `417b329a31984482027c35048db1862a10d79e1680ac23eaded8778afb88aaa7`
- Protocol target: `dd8eb34aa0cae8455ba15163831b992820461ebf`
- Review hash: `873f4435909ebc550f898972714e43ffc553b386700068ad65cecc7bef2fbbc2`

## Result

All 27,736 frozen ZIP archives and all 19 V4 manifests remain exact. Normal,
reverse and deterministic-shuffled source traversals share identity
`ca7d59b3...44aa`; the three same-reader structural traversals share
`5dfc833d...2af3`.

The preflight found 10,094 complete active-member 4h auctions and 9,690
structurally eligible decisions with a complete constant-member 24h path. The
maximum independent theoretical 24h episode ceiling is 1,405 versus the frozen
minimum 400.

The result-blind benchmark exercised the exact shared event/path evaluator on
one million synthetic rows three times. Elapsed time was 1.074372, 1.093112 and
1.079157 seconds; peak RSS remained at or below 27.234 MiB. All three outputs
share `ced8f374...f3e4`. The evaluator is a single streaming pass with no
decision-time-by-history nested scan.

OOS OHLCV values decoded, market OHLCV fields decoded during preflight,
common-state rows, candidate rows, event rows, path rows and return rows are all
zero. No network was used and no frozen production evidence was mutated.

Exactly one sealed-IS U-14 Paper observation is authorized. It is not a
strategy backtest and may not create fills, positions, equity or formal returns.
Strategy/Freqtrade code, backtesting, OOS, API/trading, `execution/live` and M2
remain prohibited.
