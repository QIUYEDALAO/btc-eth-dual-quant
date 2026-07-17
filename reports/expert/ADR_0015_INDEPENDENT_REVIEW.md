# ADR-0015 Independent Policy Review

- Verdict: `approve`
- Reviewed PR: `#105`
- Exact Draft base: `6df4aa3aa355f986e5533a51e223d69e3bf16e84`
- Exact Draft head: `03d2b8736abab277e60db1153ba73f0899d7696f`
- Draft merge commit: `e1783090dfb0a4560475b97a021ef1e77aebc399`
- Model content hash: `7acb69f72136742eb2b5f4c66e4fa09611846e74625846a690d932b9835fe78c`
- Changed-file-list hash: `73373e2fbb2a46d128e4924c732845ccdc4227d7e9b813640f9e15e33e0a430c`
- Review content hash: `893d056ec07ebc0697521a96a1533cb43265ebc2fa9484862fcdf39d8c5285a3`
- Remaining critical/high: `0 / 0`

## Executive Decision

The exact docs-only Draft is approved as policy-review evidence with zero
remaining critical or high findings. The threshold pair was frozen before
the diagnostic, every observed window clears it, and the generic predicate
fails closed outside the sole grid-aligned close-boundary defect. Accepted
events quarantine the full active-member slot, including a valid minority
row, without rewriting physical evidence.

Approval does not adopt ADR-0015. It authorizes only a separate conditional
adoption consideration under a new governance PR.

## Validation

- GitHub exact-head checks: 120/120
- Draft changed files: 15
- Fault cases hard-blocking: 16/16
- Frozen archives per traversal: 27736
- Invalid physical rows / synchronous windows: 119 / 8
- Frozen Gate: at least 2 invalid active members and fraction >= 0.80
- Minimum observed fraction: 0.933333333333
- Full-active / valid-minority windows: 7 / 1

## Review Matrix

| Dimension | Result |
| --- | --- |
| exact_head_and_ci | pass |
| docs_only_scope | pass |
| immutable_evidence_bindings | pass |
| pre_outcome_threshold_justification | pass |
| synchronous_candidate_definition | pass |
| false_positive_and_adversarial_hard_blocks | pass |
| full_slot_valid_minority_quarantine | pass |
| accounting_invariants | pass |
| v2_gap_policy_separation | pass |
| machine_fault_coverage | pass |
| authorization_non_expansion | pass |

## Informational Findings

- The 0.80 and two-member thresholds are policy parameters frozen before the diagnostic; they are not inferred from the eight observed windows.
- Full-slot quarantine intentionally discards a valid minority row to preserve a synchronized active-member panel and requires separate adoption before runtime use.

## Authorization

This review authorizes only a separate conditional-adoption consideration.
ADR-0015 remains unadopted. Production implementation, pipeline changes,
requalification, a new audit, U-04, strategy/returns/OOS, API/trading,
execution/live and M2 remain unauthorized. Any target, evidence, model,
threshold or authorization drift invalidates this approval and fails closed.
