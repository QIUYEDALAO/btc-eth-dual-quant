# U-16 Cross-Sectional Correlation-Breakdown Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U16-03-CORRELATION-BREAKDOWN-INFORMATION-PERSISTENCE-PAPER-V1`
- Protocol hash: `18e302deb6a3d9fddf8b2b5b8866d39355a95519c91f609ce670d64168f5633a`

At each completed UTC 4h decision, every active member must have a complete
48-hour sequence of completed 1h log returns. Candidate-specific peer common
returns are hourly medians excluding that candidate. Pearson correlation must
fall from at least 0.50 over the oldest 36 hours to at most 0.10 over the newest
12 hours, with a drop of at least 0.50.

The newest 12 hours must also show at least 2.40% positive relative log
displacement, at least 7 positive relative hours, no candidate hourly move
larger than 6%, and no more than half the displacement contributed by the final
hour. One event per decision and 24h connected clustering are deterministic.

The Paper observation uses only the strict next 5m open and records
1/2/4/8/12/24h path diagnostics, never fills, positions, equity or formal
returns. Data qualification, a structural ceiling and three synthetic
million-row complexity passes must pass after exact-head review and before the
unique sealed-IS observation. OOS remains sealed.
