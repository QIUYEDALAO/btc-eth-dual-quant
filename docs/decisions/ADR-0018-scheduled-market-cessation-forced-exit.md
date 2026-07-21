# ADR-0018 — Scheduled Market-Cessation Forced Exit

- Status: **Authorized for contract design and original-symbol source preflight only**
- Decision hash: `8761fabac1f32d518d6c75c08dcf0a37288262059fe3192b87fb44de836b46e9`
- Supersedes: no historical evidence
- Changes: holding/lifecycle execution semantics for one pre-announced cessation class
- Does not authorize: IS, OOS, dry-run, API, live trading, orders or M2

## Context

The fixed membership-exit authority contains 92 identities. Official daily
archives exist for 91. The missing identity is `RNDRUSDT` at the monthly
membership boundary `2024-08-01T00:00:00Z`, after Binance had already ceased
RNDR spot trading.

Binance announced the RNDR token swap and rebranding on 2024-07-10, ceased
RNDR spot trading at `2024-07-22T03:00:00Z`, and opened RENDER spot trading at
`2024-07-26T08:00:00Z`. The Render Network describes RNDR as the Ethereum token
and RENDER as the new Solana token, with a one-way 1:1 upgrade. Binance upgraded
users automatically.

This is not merely a missing URL. Substituting RENDER would cross a token,
chain, symbol and market-availability transition, and would conflict with the
repository's existing rule that a successor is provenance-only and does not
inherit history or rank.

## Decision

**Keep the official original-symbol source requirement unchanged. Change the
holding/lifecycle contract.**

For a spot market whose cessation is officially announced before the event:

1. Availability ends at the official spot trading cessation time.
2. Every open predecessor-symbol position is forcibly closed at the greatest
   exact eligible 5m open whose candle closes strictly before cessation.
3. A strategy entry scheduled for that same open is rejected; the forced exit
   has precedence.
4. No later predecessor-symbol signal or fill is permitted.
5. A successor symbol is provenance-only. It cannot supply the exit price,
   inherit the position, history or membership rank.
6. Any later readmission starts with reset and rewarm; indicator state cannot
   cross the inactive interval.

## Frozen RNDR candidate event

- predecessor: `RNDRUSDT`
- official announcement ID: `d1f2ae8d99b24439a7a900caa9bb6b3b`
- announcement date: `2024-07-10`
- cessation: `2024-07-22T03:00:00Z`
- candidate forced-exit open: `2024-07-22T02:55:00Z`
- expected candle close: `2024-07-22T02:59:59.999Z`
- required source:
  `data/spot/daily/klines/RNDRUSDT/5m/RNDRUSDT-5m-2024-07-22.zip`
- successor: `RENDERUSDT`, provenance-only
- successor trading start: `2024-07-26T08:00:00Z`
- 1:1 swap: provenance-only, never a price substitution

The timestamp is a **candidate contract value**, not validated market evidence.
The exact official archive, member and row must be independently acquired,
hashed and validated after this ADR is reviewed and merged.

## Boundary-set revision

Keep the boundary count at 92:

- retain the other 91 exact monthly boundaries;
- replace only `(RNDRUSDT, 2024-08-01T00:00:00Z)` with
  `(RNDRUSDT, 2024-07-22T02:55:00Z)`;
- compute a new canonical boundary-set hash before any performance access.

## Required validation

The implementation must bind the official announcement, archive URL/path,
archive byte size and SHA-256, ZIP member identity and SHA-256, and the exact
5m row. It must verify legal OHLCV, lifecycle/mask eligibility, independent
normal/reverse/shuffled construction, tamper negatives, complete command
evidence and zero OOS rows.

Any missing or invalid requirement remains a hard stop. No forward search,
REST substitution, successor-symbol substitution, synthetic price or last
price is permitted.

## Authorization sequence

1. Merge PR #116 only as blocked evidence after its exact-head GitHub Gate.
2. Review and merge a small ADR-0018 PR.
3. Acquire and freeze all 92 revised boundary rows.
4. Independently review and merge the completed authority.
5. Only then may original IS resume automatically under ADR-0017.

Until step 4 completes:

```text
is_trials = 0
selection_trial_count = 0
oos = false / false / 0 / 0
dry-run / API / paper-live / orders / execution-live / M2 = false
```
