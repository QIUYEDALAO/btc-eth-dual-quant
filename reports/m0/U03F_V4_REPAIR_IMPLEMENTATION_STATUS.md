# U-03F V4 Repair Implementation Status

- Status: `implementation_fixture_pass_pending_exact_head_review`
- Base main: `0e65cd41bfac590d40ae5cb0590cc7102019018c`
- Branch: `codex/u03f-v4-repair-implementation`
- Draft PR: `#98`
- Frozen protocol content hash: `9b771317d8257b397addefc262a1ffd48ded57ec1d79542372fe3c95cf8180c1`
- Repair implementation hash: `b3c17ef6b84c0c09798dd7add12ed869622a50963ab7dc99fc8d951bea063c6e`
- Frozen independent auditor algorithm hash: `7407e147cb41cbb8fbf0b0fa5b3fa08421d03f51cafb19f41c4d1541923d51f1`
- Real public requalification run: `not run`
- New independent audit run: `not run`
- Frozen source downloaded or replaced: `no`
- Historical evidence modified: `no`
- U-04 authorized: `no`
- Strategy/backtest/OOS/API/trading/execution-live/M2 authorized: `no`

## Repair Result

The production V4 authority now preserves timestamp identity through integer
milliseconds only. Strict 5m parsing validates the exact open grid and requires
`close_time == open_time + 299999`; invalid physical rows stay represented in
source provenance but are excluded from the grid and derived panel inputs, with
their parse errors and missing slots propagated fail closed.

Requalification finalization now writes the final report bytes atomically,
hashes those exact bytes into every completed build record, writes the run
manifest atomically and immediately verifies the binding. Any later report-byte
change invalidates the run.

The authoritative V4 public builder and requalification wrapper now require
the existing frozen local archive set. Download, remote replacement and
download-on-missing paths are rejected; a missing archive or source hash drift
therefore stops the later requalification instead of mutating its inputs.

New requalification evidence is routed to
`reports/m0/evidence/liquid_universe_v4_repair_requalification` and new repair-
specific report paths. The historical PR #89 evidence and reports remain
read-only; standalone previews default to ignored `storage/logs` paths.

## Frozen Fault Tests

- FT-INT-PRECISION: pass
- FT-STATIC-FLOAT-PATH: pass
- FT-ADA-INVALID-INTERVAL: pass (`8270` physical rows, `8269` valid rows)
- FT-INVALID-CLOSE-BOUNDARY: pass
- FT-REPORT-BYTE-DRIFT: pass
- FT-RUN-MANIFEST-BINDING: pass

## Integrity

- Repair protocol hash drift: none.
- Independent auditor algorithm hash drift: none.
- Historical PR #89 qualification evidence drift: none.
- Historical PR #95 failed-audit evidence drift: none.
- Source-freeze content hash: `c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`.
- Frozen source archives: `27736`.

## Gate And Stop

This is a fixture-only implementation result. The implementation PR must first
pass all CI, then a separate reviewer must bind its exact unchanged head and
return `approve` with zero critical and zero high findings. The implementation
must not merge before that review Gate. Public requalification remains a later,
separate PR and must use the unchanged fixed source range and source freeze.
It must run with `source_mode=frozen_local_only`; no archive download or
replacement is permitted.

Any head drift, protocol/auditor/source/history hash drift, failed fault test,
mismatch or critical/high review finding stops the chain. Even later successful
requalification and audit do not automatically authorize U-04.
