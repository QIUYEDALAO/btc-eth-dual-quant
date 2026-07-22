#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=".:.deps:src${PYTHONPATH:+:$PYTHONPATH}"

python3 scripts/external_strategy_original_is_authority_check.py
python3 -O scripts/external_strategy_original_is_authority_check.py
python3 scripts/external_strategy_original_is_trial_check.py
python3 -O scripts/external_strategy_original_is_trial_check.py
python3 scripts/external_strategy_original_is_preflight.py
python3 -m unittest -v \
  tests.test_external_strategy_original_is_authority \
  tests.test_external_strategy_isolation \
  tests.test_external_strategy_trial_bundle \
  tests.test_external_strategy_original_is_trial_accounting
