# U-23 Outcome-Blind Paper Protocol

- Protocol: `U23-03-RANGE-EXPANSION-CLOSE-STRENGTH-CONTINUATION-PAPER-V1`
- Status: `frozen_before_result_pending_exact_head_review`
- Protocol hash: `52807bd0e2c0bd2276c88e1d919a7e4a375c480f51fe479f0934d8c0063e5611`
- Pre-freeze synthetic feasibility: `6010529c89627e8607919272af3c85c7dd5c3fdd4e48f549b8fe055e3245637e`
- Exact core: `ffba8a38981c954024e1efa96dce3595a13a1f3be53330b9b9c776fef6881aa7`

The protocol fixes completed UTC 4h bars built from complete 5m evidence. Each
decision requires 42 prior completed ranges for every exact active member, a
current log range of at least 4%, at least twice the own-history median and at
least three robust scales above it. The same completed bar must close in its
top 10%, have a positive body covering at least 60% of its range, and exceed
the complete active-peer median return by at least 2.5%.

One deterministic representative is retained per decision and all events are
clustered into 24h connected episodes. Observation begins only at the strict
next expected 5m open and records 1/2/4/8/12/24h absolute and peer-relative
paths without fills, positions, equity or formal returns. OOS remains sealed.

Before this protocol was frozen, the exact core passed three deterministic
1,000,395-logical-bar synthetic runs. No public archive, market outcome or OOS
value was read. Only a separate exact-head independent review is authorized.
