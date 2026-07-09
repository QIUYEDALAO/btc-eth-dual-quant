# M0 Public Dual-Source Audit Unblock Design

## Status

- Design status: approved, written specification pending user review
- Phase: post-hardening review / M0 audit revalidation
- Branch: `codex/m0-dual-source-audit-unblock`
- Scope: public-data diagnostics only
- Trading approval: none

## Objective

Resolve the remaining M0 public dual-source audit blocker with reproducible,
field-level evidence from official Binance public REST and official Binance
public ZIP sources. The work must explain the recorded spot differences and
obtain valid futures dual-source evidence from at least one compliant network.

Code completion does not imply audit approval. The audit can pass only when all
required evidence exists and no blocking or unresolved difference remains.

## Current Evidence

The existing real 1-hour audit covers BTCUSDT and ETHUSDT from 2019-09-01
through 2026-07-08. It remains blocked because:

- spot ZIP/REST comparisons contain six or seven field differences and one
  timestamp-set difference per symbol;
- futures REST returned HTTP 451 on the GitHub-hosted runner, so futures
  ZIP/REST evidence was not completed.

M0 infrastructure remains accepted, but its audit status is
`audit_revalidation_required`. M1A and M1B remain `failed_validation`, and M2
remains prohibited.

## Chosen Approach

Use a multi-network, evidence-first audit. Run the same public-only comparison
locally and on the approved VPS. A source result is valid only when it uses an
official Binance public endpoint, records reproducible provenance, and does not
use credentials, proxies, VPNs, or region-bypass techniques.

Rejected alternatives:

- ZIP-only acceptance cannot satisfy a dual-source gate.
- Deferring futures while explaining only spot leaves the M0 blocker open.
- Third-party data cannot replace official Binance REST in a Binance
  ZIP-versus-REST audit.

## Scope

The audit covers BTCUSDT and ETHUSDT at the 1-hour interval for:

- `spot_klines`
- `um_futures_klines`
- `mark_price_klines`
- `index_price_klines`
- `premium_index_klines`

For every applicable dataset and symbol, evidence must include:

- the first complete month in the audit range;
- a deterministic middle month;
- the latest complete month;
- every month containing a flagged anomalous K-line;
- every month containing, or immediately adjoining, an observed gap boundary.

Duplicate selections are collapsed, but the report retains every reason that
selected a month.

## Architecture

The implementation will contain two primary units:

1. `src/btc_eth_dual_quant/data/dual_source_audit.py`
   - Pure normalization, comparison, classification, and gate logic.
   - No network access and no file-system policy.
   - Accepts source rows plus provenance and returns structured evidence.

2. `scripts/m0_dual_source_audit.py`
   - Public REST and ZIP retrieval orchestration.
   - Scope selection, local ignored evidence storage, report rendering, and
     process exit status.
   - Never reads API-key environment variables and never calls private or
     trading endpoints.

The data flow is:

```text
Official REST ----\
                   > source provenance -> canonical normalization
Official ZIP -----/                           |
                                               +-- timestamp-set comparison
                                               +-- raw-text comparison
                                               +-- Decimal numeric comparison
                                               +-- OHLCV semantic validation
                                               +-- payload hashes
                                                          |
                                               sanitized diagnostics report
```

## Canonical Comparison

### Raw Evidence Layer

For each source and selected scope, record:

- official endpoint or ZIP path category, without server or credential data;
- symbol, dataset, interval, and UTC range;
- HTTP outcome category and status code when available;
- source row count;
- SHA256 of the selected source payload;
- overlap count;
- timestamps present only in REST;
- timestamps present only in ZIP.

Full payloads remain in ignored local or VPS storage and are never included in
the committed report.

### Semantic Layer

- Convert timestamps to UTC epoch milliseconds.
- Parse prices, volumes, and comparable numeric fields with `Decimal`.
- Preserve raw source text separately from canonical numeric values.
- Validate finite values, non-negative volume, and legal OHLC ordering.
- Compare all dataset-specific fields defined by the canonical schema.
- Do not use a tolerance that can hide a genuine source value difference.

The implementation may label `1` versus `1.00000000` as a formatting
difference only when the canonical Decimal values and all semantics are equal.

## Difference Classification

Every compared row or source failure must have exactly one primary
classification:

| Classification | Definition | Gate effect |
| --- | --- | --- |
| `exact_match` | Timestamp and canonical comparable fields match. | pass |
| `format_only` | Raw strings differ but canonical values and semantics match. | explained |
| `boundary_row` | A request/month boundary row is missing on one side and is recovered from an adjacent official ZIP scope. | explained |
| `source_revision` | Official sources contain different canonical values for the same timestamp and field. | block |
| `timestamp_mismatch` | A timestamp exists on only one side and cannot be recovered from an adjacent official scope. | block |
| `invalid_ohlcv` | Numeric validity, volume, or OHLC ordering fails. | block |
| `network_blocked` | REST is unavailable, including HTTP 451 or exhausted timeout/retry policy. | block |
| `zip_unavailable` | A required official ZIP scope is absent or unreadable. | block |

Explained classifications remain visible in the report and are never deleted
from evidence.

## Network and VPS Rules

- Use only unauthenticated public `GET` resources.
- Do not request, read, print, or upload API keys.
- Do not run private smoke.
- Do not store the VPS address, SSH credentials, or server identity in reports.
- Sync code only; do not sync `.env`, raw data, DuckDB, logs, or credentials.
- Keep raw source responses under ignored storage on the execution node.
- Pull back only sanitized Markdown evidence.
- Do not use VPNs, proxies, or other region-bypass methods.
- Treat HTTP 451 as `network_blocked`; do not retry through an evasion path.
- Preserve each node's outcome independently. A successful node can provide
  valid evidence, but cannot erase a failed node's recorded diagnostic.

At least one compliant execution node must complete real REST and ZIP evidence
for every required dataset, symbol, and selected scope.

## Gate Rules

The M0 public dual-source audit passes only when all conditions are true:

- every required dataset and symbol was executed;
- every required scope reason is represented;
- official REST and ZIP evidence exists for each required comparison;
- every comparison has positive overlap;
- REST and ZIP payload SHA256 values are present;
- `network_blocked` count is zero for required evidence;
- `zip_unavailable` count is zero;
- `source_revision` count is zero;
- `timestamp_mismatch` count is zero;
- `invalid_ohlcv` count is zero;
- every observed difference is classified;
- unresolved difference count is zero.

The result remains `blocked` if the implementation and unit tests pass but any
evidence condition fails. A VPS HTTP 451 therefore produces a better explained
blocker, not an audit pass.

## Reports and Project State

Add `reports/m0/M0_DUAL_SOURCE_AUDIT_DIAGNOSTICS.md` containing:

- execution time and public-only attestation;
- dataset, symbol, interval, and scope matrix;
- per-node network outcome without node identity;
- source row counts, overlap, and one-sided timestamp counts;
- REST and ZIP payload SHA256 values;
- classification counts and field-level difference details;
- unresolved issues;
- the strict gate result.

Update `reports/m0/M0_AUDIT_REVALIDATION_REPORT.md` only from real evidence. Do
not restore M0 audit pass from fixture tests or code-completion status.

After the implementation task, update `PROJECT_STATE.yaml`,
`PROJECT_LEDGER.md`, `NEXT_ACTION.md`, and `reports/INDEX.md`. M1A and M1B
statuses must not change, and M2 must remain blocked.

## Error Handling

- Apply bounded retries only to transient public-network errors.
- Record HTTP status and sanitized error category, not response payloads.
- Fail a selected scope explicitly when parsing, schema validation, hashing, or
  comparison cannot complete.
- Never silently substitute ZIP data for missing REST evidence.
- Never silently drop malformed rows or duplicate timestamps.
- Return a non-zero process status when the strict audit gate is blocked.

## Test Plan

Add fixture-based tests that require no network for:

- `format_only` Decimal-equivalent values;
- genuine OHLCV `source_revision` differences;
- adjacent-month recovery of a `boundary_row`;
- unrecovered `timestamp_mismatch`;
- invalid OHLC ordering, negative volume, and non-finite values;
- REST HTTP 451, timeout, and ZIP-unavailable gate behavior;
- missing overlap, missing hash, missing dataset, or missing scope;
- complete evidence with zero unresolved differences;
- sanitized reporting without payloads, VPS identity, credentials, or sensitive
  environment values.

The existing test suite must continue to pass.

## Validation

Run:

```bash
PYTHONPATH=.deps:src python3 -m unittest discover -s tests -v
PYTHONPATH=.deps:src python3 -m compileall src scripts
bash scripts/m0_validate.sh
bash scripts/project_validate.sh
git diff --check
```

Run the real public audit separately:

```bash
PYTHONPATH=.deps:src python3 scripts/m0_dual_source_audit.py \
  --symbols BTCUSDT,ETHUSDT \
  --interval 1h \
  --out reports/m0/M0_DUAL_SOURCE_AUDIT_DIAGNOSTICS.md
```

The exact command may add explicit start/end or execution-node metadata flags
during implementation, but may not weaken the scope or gate described here.

## Completion Outcomes

There are two truthful completion outcomes:

1. `pass`: all mandatory official dual-source evidence is complete and every
   blocking or unresolved count is zero.
2. `blocked`: code and validation may pass, but a required source, scope, hash,
   overlap, or explanation remains incomplete.

Neither outcome changes M1A or M1B from `failed_validation`, approves M2, or
permits live trading, real-API paper trading, order operations, simulated
matching, API permissions, or `execution/live`.

