#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/external_strategy_boundary_authority_build.py
python3 -O scripts/external_strategy_boundary_authority_build.py
python3 -m unittest -q tests.test_external_strategy_boundary_authority_complete
