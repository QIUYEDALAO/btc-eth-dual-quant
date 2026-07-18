#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-.deps:.venv/lib/python3.12/site-packages:src}"
python3 scripts/u15_design_authorization_check.py
python3 -m unittest tests.test_u15_design_authorization -v
