#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${ROOT}/.deps:${ROOT}/src:${ROOT}"

"${PY_CMD}" "${ROOT}/scripts/adr0015_invalid_interval_audit_protocol_check.py"
"${PY_CMD}" "${ROOT}/scripts/adr0015_independent_auditor_check.py"
"${PY_CMD}" -m unittest -v \
  tests.test_adr0015_independent_auditor \
  tests.test_adr0015_invalid_interval_audit_protocol \
  tests.test_u03f_v4_repair_exact_head_review
"${PY_CMD}" -m compileall -q \
  "${ROOT}/src/btc_eth_dual_quant/audit/liquid_universe_v4_adr0015.py" \
  "${ROOT}/src/btc_eth_dual_quant/audit/liquid_universe_v4_adr0015_audit_run.py" \
  "${ROOT}/scripts/adr0015_independent_audit_run.py"
