# Liquid Spot Universe V2 Correctness Hardening

- Status: implementation_pass_pending_public_requalification
- Contract: `LIQUID-SPOT-USDT-TOP15-V2`
- V1 admission status: `superseded_pending_v2_requalification`
- Public V2 requalification executed: no
- Independent audit executed: no

## Correctness Changes

- Asset exclusions use a versioned registry with effective dates; ticker suffixes are not an exclusion authority.
- `USD1` and stable-value assets are excluded; `PAXG` is excluded as a commodity-backed reference asset; `JUP` remains eligible by name.
- Monthly daily ZIP evidence is primary; daily ZIP evidence is fill-only and conflicting or duplicated evidence blocks.
- Eligibility requires the immediately preceding 365 complete UTC days and ranking requires the immediately preceding 90 complete UTC days.
- Input hashes bind symbol, date, quote volume, authority, archive SHA256, and contract version.
- Complete expected 5m grids detect missing whole hours, partial hours, duplicates, off-grid rows, invalid timezones, invalid OHLC, and invalid volume.
- Gap attribution defaults to unresolved. Global classification requires documented evidence or the frozen synchronized threshold with every participating archive verified.
- Global quarantine applies to every member in the month; confirmed symbol gaps quarantine the full symbol-month without replacement.
- Machine JSON artifacts are the only qualification authority; Markdown is generated output only.
- Qualification output cannot authorize a hypothesis, strategy, event scan, returns, backtesting, OOS, API/trading, or M2.

## Remaining Gate

PR-B must rebuild the fixed 2020-01 through 2026-06 public evidence twice and prove cold/warm deterministic equality. PR-C must independently reproduce membership, quarantine, and qualified-panel results. U-04 remains unauthorized until both stages pass and merge.
