# M0 Validation Status

generated_utc: 2026-07-08T23:36:19+00:00

## Commands

```bash
PYTHONPATH=.deps:src python3 -m unittest discover -s tests -v
PYTHONPATH=.deps:src python3 -m compileall src scripts
bash scripts/m0_validate.sh
```

## Results

- unittest: 24 tests OK
- compileall: OK
- bash scripts/m0_validate.sh: PASS=6 FAIL=0
- read-only scan: clean
- execution/live scan: clean
- secret scan: clean
- secret scan note: `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `api_key`, and `api_secret` variable-name references are allowed; no real key, secret, private key, or `sk-` token was found.
- git diff --check: clean
- Private smoke: not_run
- M1 Gate: blocked
