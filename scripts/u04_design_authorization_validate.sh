#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHONPATH="${PYTHONPATH:-}:$ROOT/.deps:$ROOT/src" python3 scripts/u04_design_authorization_check.py
PYTHONPATH="${PYTHONPATH:-}:$ROOT/.deps:$ROOT/src" python3 -m unittest -v tests.test_u04_design_authorization
