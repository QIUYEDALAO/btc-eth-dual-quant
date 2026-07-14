# ADR-0012: Liquid Universe Qualification Correctness V2

- Status: accepted for correctness hardening and public-data requalification only
- Date: 2026-07-14
- Contract: `LIQUID-SPOT-USDT-TOP15-V2`
- Supersedes: V1 qualification admission decision after V2 requalification; V1 evidence remains immutable historical evidence

## Context

The V1 public qualification run established a useful point-in-time universe, but its implementation is not strong enough to authorize downstream research. Known defects include incomplete machine enforcement of asset categories, suffix-based false positives, Markdown used as a computation input, incomplete fail-closed handling of missing local archives, marker-only report checks, an incorrect strategy-authorization output, and incomplete machine proof of missing-hour and quarantine scope.

V1 is therefore `superseded_pending_v2_requalification`. Its reports and hashes are retained and must not be rewritten.

## Decision

V2 fixes correctness, provenance, deterministic reconstruction, quarantine application, and authorization boundaries. It does not change the research choices frozen by ADR-0011:

- rebuild membership monthly at UTC month start;
- rank by median daily quote volume over the prior 90 complete UTC days;
- require the immediately preceding 365 complete UTC days;
- target 15 members without replacing ineligible assets;
- break ties by ascending symbol;
- preserve point-in-time membership and delisted history;
- use Freqtrade as the only future strategy-return engine.

The versioned asset registry is the only exclusion authority. Leveraged tokens require explicit registry evidence; ticker suffixes alone are not evidence. Stable-value, fiat-pegged, commodity-backed or external-reference, wrapped, staked/receipt, and duplicate representations are excluded while their registry record is effective. `PAXG` is excluded as a commodity-backed external-reference asset. `JUP` is not excluded merely because its ticker ends in `UP`.

Monthly official ZIP archives remain primary. Daily official ZIP archives may fill a missing date only and may never overwrite or disagree with monthly evidence. REST remains sampled evidence only. Any missing, corrupt, unverified, duplicated, conflicting, non-UTC, non-finite, negative, or structurally invalid input fails closed.

Every selected symbol-month is checked against the complete expected 5m UTC grid. Documented or sufficiently synchronized exchange-wide gaps may be quarantined only after all participating archives are successfully verified. A confirmed symbol-specific archive termination quarantines the entire symbol-month without replacement. Every other gap remains blocked.

Machine JSON manifests are the only active qualification authority. Markdown is generated from those manifests and is never an input. Contract, registry, source, membership, quarantine, qualified-panel, and summary content use canonical JSON SHA256 identities that exclude paths, clocks, worker ordering, and temporary state.

## Authorization

V2 authorizes data qualification only. Strategy selection, event scanning, signals, returns, OOS access, Freqtrade backtesting, API/trading, M2, and U-04 remain false until V2 public requalification and an independent audit both pass in later PRs.

Any change to Top 15, 90 days, 365 days, category policy, ranking authority, activation timing, or gap policy requires a new ADR.
