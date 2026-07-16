#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON:-python3}"
export PYTHONPATH=".:.deps:src${PYTHONPATH:+:$PYTHONPATH}"

bash scripts/liquid_universe_v4_implementation_validate.sh
"$PYTHON_BIN" -m unittest \
  tests.test_liquid_universe_v4_public_run \
  tests.test_liquid_universe_v4_requalification -v
"$PYTHON_BIN" scripts/liquid_universe_v4_requalification_check.py
"$PYTHON_BIN" -m compileall src scripts
bash scripts/project_validate.sh

order_word="ord""er"
fill_word="fi""ll"
engine_word="eng""ine"
forbidden_pattern="(/api/v3/${order_word}|/fapi/v1/${order_word}|/sapi/v1/margin/${order_word}|place_${order_word}|cancel_${order_word}|create_${order_word}|simulate_${fill_word}|matching_${engine_word})"
if find src scripts -type f -name '*.py' -print0 | xargs -0 grep -n -E "$forbidden_pattern" ; then
  echo "FAIL no-trading scan"
  exit 1
fi
test ! -e src/execution/live
test ! -e execution/live
"$PYTHON_BIN" scripts/m0_secret_scan.py
git diff --check
echo "V4 requalification validate PASS"
