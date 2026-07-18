# U-05 Cross-Sectional Breadth-Demand Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Candidate: `U05-CROSS-SECTIONAL-BREADTH-DEMAND-PERSISTENCE`
- Protocol content hash: `c8bd5523e94fc410e6ed4e5a28bb81864ed648d85c9d039ba26aab6dd8bae214`
- Public data read or event scan executed: no
- Path or return result accessed: no
- OOS opened: no

## Frozen event

At each completed UTC-aligned 4h block, every exact active member must have the
current and prior completed 4h close, each backed by four complete constituent
1h bars. At least 10 active members are required. An event requires both:

- at least 80% positive members, enforced as `positive × 5 >= active × 4`;
- cross-sectional median simple 4h return of at least `+1.20%`.

The denominator always contains all active members. Missing, duplicate,
quarantined, non-member or lifecycle-ambiguous rows make the timestamp
ineligible; no replacement or current-membership backfill is allowed.

## Episode and observation

Candidate timestamps form global connected 24h episodes; only the first event
is retained. The reference is the first expected 5m open strictly after the
completed decision, with no later search if missing. The event-time active
basket is held fixed only for diagnostics at 1h, 2h, 4h, 8h, 12h and 24h.

The protocol records median cross-sectional close displacement, positive-member
fraction, median-path MFE/MAE and first Base-cost recovery time. Any missing,
quarantined or lifecycle-intersecting member right-censors the event. These are
Paper path diagnostics, not fills, positions, equity or formal strategy return.

## Frozen Gates

- At least 90 complete independent IS episodes.
- Projected full/OOS episodes at least 120/30 without reading OOS.
- At least three years with 10 episodes; one year at most 45%.
- One calendar quarter at most 25%; at least 24 distinct event months.
- Median 24h common-demand close displacement at least `+1.80%`.
- Median 24h positive-member fraction at least `60%`.
- Qualification, quarantine, lifecycle and order mismatches exactly zero.

Roundtrip cost references are Base `0.30%`, Cost×2 `0.60%`, Stress A `0.80%`
and Stress B `1.10%`.

## Authorization

Only an exact-head independent review may follow. Data qualification, event
scan, path observation, signals, formal returns, fixed rules, Freqtrade code,
backtesting, OOS, API/trading, `execution/live` and M2 remain unauthorized.
