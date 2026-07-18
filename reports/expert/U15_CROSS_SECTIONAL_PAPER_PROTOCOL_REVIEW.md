# U-15 Cross-Sectional Paper-Protocol Exact-Head Review

- Verdict: `approve`
- Target: `5438dec609aaaed675e8ecba6f15ae9bb6f6da5a`
- Protocol hash: `3b58d6a23cc78e3b644d935599e625c04267317d42608adf2f0321ec51ab577a`
- Critical/high findings: `0/0`
- Review hash: `2686c3acc1f5d46d7b37295530c54268f314cca177197306db7358bb8aa38ceb`

The exact target binds official taker-buy quote volume rather than inferring
trade direction from price, total volume or trade count. It requires every
consumed field and raw row to pass a separate frozen-source semantic and
availability qualification before any state or event calculation. Missing,
ambiguous or revised fields fail closed without repair or substitution.

Completed 4h timing, all-member cross-sectional median/MAD, fixed event
thresholds, deterministic tie-break, 24h connected clustering, strict next-5m
reference, peer paths and right-censoring are causal and internally complete.
The fixed sample, distribution, economic, complexity and isolation Gates are
specified before results.

Approval authorizes only a separate field/data qualification, synthetic
complexity benchmark and result-free scope preflight. It does not authorize
taker-state/event/path scanning, formal returns, strategy rules, OOS or trading.
