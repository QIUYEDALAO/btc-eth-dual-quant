#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=".deps:src" python3 scripts/u05_design_authorization_check.py
PYTHONPATH=".deps:src" python3 -m unittest -v tests.test_u05_design_authorization
