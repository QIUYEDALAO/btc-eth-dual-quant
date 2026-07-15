#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-.deps:src:.}"
bash scripts/liquid_universe_contract_validate.sh
python3 -m unittest tests.test_liquid_universe_qualification -v
python3 -m unittest tests.test_universe_gap_attribution -v
python3 -m unittest tests.test_liquid_universe_end_to_end -v
python3 -m unittest tests.test_liquid_universe_fault_injection -v
python3 scripts/project_state_transition_check.py
if [[ -f reports/m0/evidence/liquid_universe_v2/qualification_summary.json ]]; then
  python3 scripts/liquid_universe_qualification_check.py
  python3 scripts/liquid_universe_gap_attribution_check.py
fi
python3 -m compileall src scripts
python3 scripts/m0_secret_scan.py
test -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)"
git diff --check
echo "LIQUID_UNIVERSE_QUALIFICATION_VALIDATE PASS"
