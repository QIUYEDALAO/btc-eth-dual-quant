#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/u18_design_authorization_check.py
PYTHONPATH=.deps:src python3 -m unittest tests.test_u18_design_authorization
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
git diff --check
