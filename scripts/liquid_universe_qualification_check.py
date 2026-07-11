#!/usr/bin/env python3
from pathlib import Path
def main():
    text=Path('reports/m0/LIQUID_SPOT_UNIVERSE_QUALIFICATION_REPORT.md').read_text()
    required=['- Status: implementation_pass_runtime_qualification_pending','- Strategy/events/signals/returns computed: no','- OOS accessed: no','- M2 authorized: no','- Runtime artifacts committed: no']
    missing=[x for x in required if x not in text]
    if missing:
        print('liquid_universe_qualification_check FAIL',*missing,sep='\n- '); return 1
    print('liquid_universe_qualification_check PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
