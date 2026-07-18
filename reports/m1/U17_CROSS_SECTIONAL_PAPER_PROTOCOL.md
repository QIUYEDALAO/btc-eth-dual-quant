# U-17 Cross-Sectional Liquidity-Risk Premium Paper Protocol

- Status: `frozen_before_result_pending_exact_head_review`
- Protocol: `U17-03-LIQUIDITY-RISK-PREMIUM-PAPER-V1`
- Protocol hash: `815013384df29fe2e803ee3e9dde22d0561cf1b67a24504290344ddef1ee6089`

At each completed UTC day, every decision-time active member must have 28
complete UTC days, each reconstructed from exactly 288 qualified 5m rows.
Daily quote volume is ranked ascending across the complete active set. A
candidate must remain in the lowest liquidity quartile on at least 21 of the
28 days; the most persistently illiquid representative is chosen without using
price direction or a membership entry/exit event.

Events are connected across all symbols over 28 days and only the first is an
independent episode. The strict boundary 5m open anchors 1/3/7/14/28-day path
diagnostics. The primary Paper Gates require 40 complete independent IS
episodes, adequate time/symbol dispersion, median 28-day relative and absolute
displacements of at least 1.80%, and at least 60% positive relative outcomes.

This is a Paper observation only: no fills, position, equity or formal return.
Exact-head review must approve the protocol before result-free source
qualification, sample-ceiling proof and three synthetic million-row complexity
passes. OOS remains sealed.
