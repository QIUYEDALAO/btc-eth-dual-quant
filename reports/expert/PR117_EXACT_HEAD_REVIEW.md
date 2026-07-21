# PR #117 Exact-Head Independent Review

## Target

- Repository: `QIUYEDALAO/btc-eth-dual-quant`
- Pull request: `#117`
- Reviewed exact head: `bb22a08cc7bcd31c458ca7d362e536d88c0ca1e2`
- Handoff-requested head: `30cca38018017e0b1f74763c2861d9fee60c7026`
- Base: `d2c54d5d81e1e323d9581904df015afe368e6440`
- ADR-0018 canonical hash: `8761fabac1f32d518d6c75c08dcf0a37288262059fe3192b87fb44de836b46e9`

The handoff head is one context-only commit behind the current GitHub head. This
review is anchored to the actual current head, not the stale head written in the
handoff or PR body.

## Verdict

**APPROVE**

- Critical findings: **0**
- High findings: **0**

## Review conclusions

1. **Forced-exit timing — PASS.** The contract derives the forced-exit open
   `2024-07-22T02:55:00Z` from the officially announced RNDR spot cessation at
   `2024-07-22T03:00:00Z`; the expected 5m close is
   `2024-07-22T02:59:59.999Z`. The archive and row remain explicitly
   unvalidated market evidence.

2. **Same-open precedence — PASS.** Every already-open predecessor position is
   closed first; a new entry scheduled for the same open is rejected; later
   predecessor signals and fills are forbidden.

3. **RNDR/RENDER isolation — PASS.** `RENDERUSDT` is provenance-only and cannot
   provide the RNDR exit price, inherit the position, history, or membership
   rank. Any later readmission resets and rewarms indicator state.

4. **Boundary revision — PASS.** Exactly one result-blind replacement keeps the
   identity count at 92: remove
   `(RNDRUSDT, 2024-08-01T00:00:00Z)` and add
   `(RNDRUSDT, 2024-07-22T02:55:00Z)`. A new canonical boundary-set hash is
   mandatory before performance access.

5. **NB-01 — PASS.** The contract explicitly requires genuinely independent
   normal, reverse, and deterministic-shuffled constructions for the later
   completed authority.

6. **Permissions — PASS.** This PR does not authorize archive acquisition,
   authority freeze, original or modified IS, selection materialization, OOS,
   dry-run, API/private endpoints, paper/live, orders, `execution/live`, or M2.

7. **PR #116 dependency — PASS.** The reviewed PR #116 head
   `edf753f28f26f6a168798fa40b49bcbd121a2adc` is recorded as Gate run `29829112223` success and merged as
   `d2c54d5d81e1e323d9581904df015afe368e6440` before this ADR branch.

## Exact-head merge authorization

PR #117 may be merged only after:

1. it is marked Ready without changing the head;
2. the GitHub Gate succeeds on exact head `bb22a08cc7bcd31c458ca7d362e536d88c0ca1e2`;
3. the head still equals `bb22a08cc7bcd31c458ca7d362e536d88c0ca1e2` at merge time.

Any new commit invalidates this review.

Merging ADR-0018 authorizes only the subsequent one-item official RNDR archive
and exact-row preflight. It does not itself authorize downloading the other 91
archives, freezing the completed boundary authority, or running IS.

## Non-blocking notes

- The PR body and handoff still identify `30cca380…`; update the PR metadata to
  the reviewed head without creating a commit.
- The one commit after `30cca380…` changes only required project-context files;
  the ADR document, machine contract, checker, and ADR tests are unchanged.
- The current reviewed head has no GitHub workflow run yet.

## GitHub write status

Attempts to submit the formal APPROVE review and mark the PR Ready both failed
with `Resource not accessible by integration`. The review therefore exists as
this signed-off artifact but has not been posted to GitHub.

## Safety state

```text
IS trials             = 0
selection trials      = 0
OOS                    = false / false / 0 / 0
archive acquisition   = false
dry-run/API/live/M2   = false
```

Machine review content hash:

`41f4360976a3b2dff2408bf3262fff548b23b3bf1460314d3c8882c1e9ad780f`
