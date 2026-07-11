# M1E IS Data Isolation Report

- Status: pass
- Scope: M1E-05 IS data isolation only
- Candidate evaluated: no
- Signals selected: no
- Strategy returns computed: no
- OOS OHLC parsed: no
- OOS opened: no
- IS start: 2020-07-01T00:00:00Z
- IS end exclusive: 2024-09-11T00:00:00Z
- Source manifest SHA256: `c8b15858bd7cb7467fdc0e9067c9e7494e724a08af49762bfd72ad2c9528bba8`

## Snapshots

| Dataset | Rows | Gaps | Segments | SHA256 |
| --- | ---: | ---: | ---: | --- |
| BTCUSDT:1h | 36763 | 11 | 12 | `b33e66ad488550b3f65d8ff928585adac584bd3ad007d00f4738d4c10f6393bf` |
| BTCUSDT:4h | 9181 | 11 | 12 | `dc0653cb7b45bb7321b65715fc42c3441ffb0dbc0b7d9ca735e8ddd335ab06ed` |
| ETHUSDT:1h | 36763 | 11 | 12 | `037f47f80fea276ede9bea5519f9f61dc3b0453fd99871e996773d49a08087e2` |
| ETHUSDT:4h | 9181 | 11 | 12 | `99d5e3e47cb4cd6878a48f8ef25dc28132de99ae5b620a84a3f113bd629c4a9d` |

## Gate

- IS boundary enforcement: pass
- Incomplete/future/duplicate bar rejection: pass
- Gap segmentation: pass
- Rewarm parameter selected: no
- M1E-06 paper diagnostics authorized: yes
- Fixed strategy rules authorized: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

The ignored snapshots expose segment age so a later frozen contract can reject bars before its complete lookback is rebuilt. No fill or interpolation is performed.
