#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHONPATH=.deps:src python3 scripts/u17_cross_sectional_data_qualification_check.py
PYTHONPATH=.deps:src python3 -m unittest tests.test_u17_cross_sectional_data_qualification
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
git diff --check
