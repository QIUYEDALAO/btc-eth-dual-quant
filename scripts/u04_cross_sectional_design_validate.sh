#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=".deps:src" python3 scripts/u04_cross_sectional_design_check.py
PYTHONPATH=".deps:src" python3 -m unittest -v tests.test_u04_cross_sectional_design
grep -qE '^- Status: `economic_hypothesis_pass_protocol_design_only`$' reports/m1/U04_CROSS_SECTIONAL_RESIDUAL_REVERSAL_DESIGN.md
grep -qE '^- Candidate events evaluated: no$' reports/m1/U04_CROSS_SECTIONAL_RESIDUAL_REVERSAL_DESIGN.md
grep -qE '^- Formal returns computed: no$' reports/m1/U04_CROSS_SECTIONAL_RESIDUAL_REVERSAL_DESIGN.md
grep -qE '^- OOS opened: no$' reports/m1/U04_CROSS_SECTIONAL_RESIDUAL_REVERSAL_DESIGN.md
grep -qE '^- Status: `pass_design_level`$' reports/m1/U04_NON_DUPLICATION_REVIEW.md
grep -qE '^- Prior failed outcome used to select rules: no$' reports/m1/U04_NON_DUPLICATION_REVIEW.md
