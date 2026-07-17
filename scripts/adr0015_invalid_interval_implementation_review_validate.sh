#!/usr/bin/env bash
set -euo pipefail

PY_CMD="${PYTHON:-python3}"
ROOT="$(git rev-parse --show-toplevel)"
TARGET_HEAD="67e7d29eaed63a3edb903dd618184bc9f02c5748"
TARGET_REF="refs/remotes/origin/adr0015-invalid-interval-implementation-reviewed-head"
TARGET_DIR="$(mktemp -d)"
trap 'rm -rf "$TARGET_DIR"' EXIT

export PYTHONPATH="${ROOT}/.deps:${ROOT}/src:${ROOT}"

git fetch origin "+refs/pull/109/head:${TARGET_REF}"
test "$(git rev-parse "${TARGET_REF}")" = "$TARGET_HEAD"
ADR0015_REQUIRE_IMPLEMENTATION_HEAD=1 "$PY_CMD" scripts/adr0015_invalid_interval_implementation_review_check.py
"$PY_CMD" -m unittest tests.test_adr0015_invalid_interval_implementation_review -v

git archive "$TARGET_HEAD" | tar -x -C "$TARGET_DIR"
(
  cd "$TARGET_DIR"
  export PYTHONPATH="${ROOT}/.deps:${TARGET_DIR}/src:${TARGET_DIR}"
  "$PY_CMD" -m unittest tests.test_adr0015_invalid_interval_policy -v
  "$PY_CMD" -m unittest tests.test_liquid_universe_v4_public_run tests.test_u03f_v4_repair_implementation -v
  "$PY_CMD" scripts/adr0015_invalid_interval_implementation_check.py
  "$PY_CMD" -m compileall -q src scripts
)

"$PY_CMD" scripts/project_context_check.py
"$PY_CMD" scripts/project_state_transition_check.py
"$PY_CMD" scripts/m0_secret_scan.py
git diff --check origin/main...HEAD

changed="$(git diff --name-only origin/main...HEAD)"
invalid="$(printf '%s\n' "$changed" | rg -v '^(AGENTS\.md|NEXT_ACTION\.md|PROJECT_EXECUTION_CHECKLIST\.md|PROJECT_LEDGER\.md|PROJECT_STATE\.yaml|reports/INDEX\.md|reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS\.md|reports/expert/ADR_0015_INVALID_INTERVAL_IMPLEMENTATION_REVIEW\.md|reports/expert/evidence/adr0015_invalid_interval_implementation_review\.json|scripts/project_state_transition_check\.py|scripts/adr0015_invalid_interval_implementation_review_(check\.py|validate\.sh)|tests/test_adr0015_invalid_interval_implementation_review\.py|tests/test_liquid_universe_v3_klay_conflict\.py)$' || true)"
test -z "$invalid"

echo "adr0015_invalid_interval_implementation_review_validate PASS"
