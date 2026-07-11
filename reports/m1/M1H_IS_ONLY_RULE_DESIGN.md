# M1H IS-Only Rule Design

- Status: economic_hypothesis_pass_paper_protocol_only
- Candidate: FUNDING-EXTREME-SPOT-CONTRARIAN
- Scope: economic hypothesis, public-data lineage, timing legality and non-duplication only
- Selected hypothesis route: settlement-aligned negative funding extreme plus later spot contrarian observation
- Spot-only signal family: yes
- Futures position used: no
- Funding cashflow captured: no
- Two-leg execution used: no
- Candidate events evaluated: no
- Rule parameters selected: no
- Formal strategy returns computed: no
- OOS opened: no
- Strategy code authorized: no
- Freqtrade backtesting authorized: no
- M2 authorized: no

## Economic Hypothesis

M1H studies whether an extreme **settled negative funding observation** can
identify derivatives short crowding and pessimistic positioning that later
unwinds into spot price appreciation. Funding is an information input only. A
future strategy, if separately approved, would hold spot or cash and would not
receive funding, short a perpetual, hedge basis, or run two-leg execution.

The prospective return source is a later spot-price rebound after derivatives
crowding exhausts. It is not funding carry, basis convergence, leverage, market
making, or the direct reversal of a spot-price panic candle. This design selects
the economic route and funding sign only; it does not select an extreme
threshold, lookback, confirmation, timeframe, entry, exit, stop, size or
cooldown.

## Failure Regimes

- Negative funding can correctly reflect durable adverse information rather than temporary crowding.
- Extreme observations can be too sparse for the frozen 120/30 paper sample budget.
- Funding cadence or publication timing can be incomplete, revised or inconsistent.
- A later spot rebound can be too small to cover the frozen stressed roundtrip cost.
- BTC and ETH observations can be one correlated stress episode rather than independent evidence.
- A proposed exit can depend on intrabar ambiguity or optimistic gap fills that Freqtrade cannot represent conservatively.

Paper opportunity is not realizable edge. M1G proved that MFE or a favorable
path envelope cannot substitute for an implementable lifecycle, daily-MTM
equity and cost-aware validation.

## Timing Legality

- A historical funding event is unavailable before its `fundingTime` settlement timestamp.
- A decision may include that event only at or after `fundingTime`.
- Any future entry must occur at a canonical spot bar open strictly later than `fundingTime` and must not precede the decision timestamp.
- A spot bar sharing the settlement timestamp is not a legal fill.
- Future funding observations, future spot bars and an incomplete current bar are prohibited.
- No fixed funding interval is assumed. Every event must retain its inferred cadence.

## Data Lineage

| Purpose | Public authority | Allowed fields | Design-stage use |
| --- | --- | --- | --- |
| Primary sentiment observation | M0 `funding_rate_history`, `GET /fapi/v1/fundingRate` | `symbol`, `fundingRate`, `fundingTime`, `markPrice` | Identity, sign, settlement time and future protocol input family only |
| Funding cadence | `fundingInfo` then multiple `premiumIndex.nextFundingTime` cadence then adjacent historical settlement times | interval metadata only | Per-event normalization requirement; no hardcoded default |
| Spot observation | M0 canonical public spot OHLC | future completed OHLC only | Later outcome and execution evidence; cannot independently create an M1H event |

A single `premiumIndex` snapshot is not a complete interval. Private income,
commission, balances, account payloads and API credentials are outside scope.
This design review performs no network access and reads no market outcomes.

## Deferred Decisions

The negative-funding extreme definition, normalization lookback, interval-aware
normalization, optional post-settlement spot condition, timeframes, entry bar,
exit family, holding limit, stop, position cap, clustering, cooldown and warmup
remain unresolved. There is no range, candidate list, grid or hyperopt space.

## Execution Representability

Before implementation, a separately reviewed exit family must avoid dependence
on same-bar target/stop ordering and optimistic gap fills. It must produce zero
timestamp mismatch on deterministic conservative fixtures. Freqtrade remains
the sole single-leg return authority; Python may audit but may not become a
second strategy engine. No exit family is selected by this review.

## Decision

The economic mechanism, lineage and timing boundary are coherent enough to
authorize only a separate pre-outcome M1H paper-protocol design. This report
does not authorize an event scan, fixed rules, strategy code, returns, OOS,
private data, dry-run/live, orders, execution or M2.
