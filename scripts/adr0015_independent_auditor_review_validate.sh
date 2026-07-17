#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHONPATH="${PYTHONPATH:-}:$ROOT/.deps:$ROOT/src" python3 scripts/adr0015_independent_auditor_review_check.py
PYTHONPATH="${PYTHONPATH:-}:$ROOT/.deps:$ROOT/src" python3 -m unittest -v tests.test_adr0015_independent_auditor_review tests.test_adr0015_independent_auditor
