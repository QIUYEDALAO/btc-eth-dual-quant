#!/usr/bin/env bash
set -euo pipefail

python3 scripts/u14_cross_sectional_paper_protocol_review_check.py
python3 -m unittest tests.test_u14_cross_sectional_paper_protocol_review -v
