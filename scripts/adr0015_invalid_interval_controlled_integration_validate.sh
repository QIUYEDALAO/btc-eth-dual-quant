#!/usr/bin/env bash
set -euo pipefail

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH=".:.deps:src${PYTHONPATH:+:$PYTHONPATH}"

"$PY_CMD" scripts/adr0015_invalid_interval_controlled_integration_check.py
"$PY_CMD" scripts/adr0015_invalid_interval_implementation_check.py
"$PY_CMD" -m unittest tests.test_adr0015_invalid_interval_policy
git diff --check

echo "adr0015_invalid_interval_controlled_integration_validate PASS"
