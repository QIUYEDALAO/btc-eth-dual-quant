#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
PYTHONPATH=.deps:src python3 scripts/u21_cross_sectional_paper_protocol_check.py
PYTHONPATH=.deps:src python3 -m unittest tests.test_u21_cross_sectional_paper_protocol
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
PYTHONPATH=.deps:src python3 -m unittest discover -s tests -q
python3 -m compileall -q src scripts
[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]
python3 scripts/m0_secret_scan.py
git diff --check
