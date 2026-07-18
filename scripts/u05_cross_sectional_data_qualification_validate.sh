#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/u05_cross_sectional_data_qualification_check.py
python3 -m unittest -v tests.test_u05_cross_sectional_data_qualification
python3 scripts/u05_cross_sectional_paper_protocol_review_check.py
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
git diff --check
