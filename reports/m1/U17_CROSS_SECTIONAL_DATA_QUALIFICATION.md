# U-17 Frozen-Source Data Qualification and Preflight

- Status: `failed_pre_result_sample_ceiling`
- Contract hash: `936e7ac34d3da3db729a8276813eae05b651b800b62dcece037008d189872fd5`
- Failure evidence hash: `434d8a58a19306e9ff340da3b8df0c85fe15848c2686ed15491dee05ac64af91`

All 27,736 frozen archives and 19 manifests remain exact. Normal, reverse and
deterministic-shuffled structural readers have the same identity. Three
one-million-logical-row synthetic evaluator passes are deterministic and stay
below 0.10 seconds and 27.141 MiB.

The result-free structural ceiling fails. Only 13 daily decisions can satisfy
the frozen 28-day history plus 28-day future-path requirement while keeping the
exact active membership constant. After the frozen 28-day connected clustering,
the maximum is 3 independent episodes, below the preregistered minimum 50.

No quote-volume or price field was decoded during preflight. Liquidity ranks,
candidates, events, paths, returns and OOS values are all zero. The first
attempt raised the ceiling failure before writing evidence; the runner was
changed only to serialize the same fail-closed metadata outcome, and the
deterministic evidence run again observed 3. No Gate, protocol or evaluator
rule changed.

U-17 is permanently closed before Paper results. No Paper observation, protocol
relaxation, second admission attempt, fixed rule, strategy, backtest or OOS is
authorized.
