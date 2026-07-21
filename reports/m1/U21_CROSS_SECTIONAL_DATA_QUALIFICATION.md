# U-21 Frozen-Source Data Qualification

- Status: `failed_pre_result_complexity`
- Contract hash: `7e159601a935a90d4ac156bb64f2fa379abca5bedb4471570e43aef348d9ee5c`
- Failure evidence hash: `33e53b7fd32c6610349f99bb01cf71143ab9837289198266fd1b25f6e7147a1b`

The first required one-million-row synthetic pass of the exact U-21 evaluator
triggered the frozen combined time/RSS/input-count complexity guard. The
qualification runner stopped before opening any frozen source archive, so zero
market prices, returns, common adjustments, cokurtosis values, events, paths or
OOS values were decoded.

The protocol fixes three passing synthetic runs before any Paper observation.
That prerequisite failed. No optimization, retry, threshold change or second
qualification is authorized; U-21 is closed before results. No strategy,
backtest, OOS, trading or M2 authority exists.
