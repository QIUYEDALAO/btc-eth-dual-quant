# M0 Validation Status

generated_utc: 2026-07-09T02:03:06+00:00

## Commands

```bash
PYTHONPATH=.deps:src python3 -m unittest discover -s tests -v
PYTHONPATH=.deps:src python3 -m compileall src scripts
bash scripts/m0_validate.sh
```

## Results

- unittest: 26 tests OK
- compileall: OK
- bash scripts/m0_validate.sh: PASS=6 FAIL=0
- read-only scan: clean
- execution/live scan: clean
- secret scan: clean
- secret scan note: `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `api_key`, and `api_secret` variable-name references are allowed; no real key, secret, private key, or `sk-` token was found.
- git diff --check: clean
- GitHub Actions CI: `.github/workflows/m0-validate.yml` added for pull_request and push using Python 3.11 and `bash scripts/m0_validate.sh`
- anomaly review: explained_market_move=47, unresolved=0
- Zero unexplained anomalies: pass
- Private smoke: not_run
- M1 Gate: blocked
