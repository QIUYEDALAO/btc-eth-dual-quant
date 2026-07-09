# M0 Public Dual-Source Audit Unblock Implementation Plan

## Scope

Implement the approved public-only, multi-network audit in
`docs/superpowers/specs/2026-07-10-m0-dual-source-audit-unblock-design.md`.
No strategy, private API, credential, execution, order, or M2 work is included.

## Tasks

1. Add fixture tests for exact Decimal comparison, formatting-only differences,
   boundary recovery, source revision, timestamp mismatch, invalid OHLCV,
   unavailable sources, strict coverage gates, and report sanitization.
2. Add a pure `dual_source_audit` module with structured scope evidence,
   deterministic hashes, classification, serialization, aggregation, and gate
   evaluation.
3. Add a public-only CLI that profiles official monthly ZIP data, selects
   first/middle/latest/anomaly/gap scopes, fetches matching official REST rows,
   stores raw responses under ignored append-only run directories, and emits
   sanitized JSON/Markdown evidence.
4. Add a manual GitHub workflow that uses no secrets and preserves a blocked
   result as a failed evidence run rather than an audit pass.
5. Run local evidence collection, inspect every source difference, and run the
   same command on the approved VPS when credential-free SSH access is
   available.
6. Merge per-node sanitized evidence, update the M0 audit report truthfully,
   update project context files, run all validations, and publish the branch.

## Verification

- Full unittest discovery and compileall.
- `scripts/m0_validate.sh` and `scripts/project_validate.sh`.
- Secret, no-trading, and execution/live scans included by validation scripts.
- Real public audit result kept distinct from fixture and code validation.
- Git tracks no raw data, DuckDB, logs, local reports, credentials, or runtime
  artifacts.

