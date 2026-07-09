# Reports Index

| Report | Phase | Status | Meaning | Approves Trading |
| --- | --- | --- | --- | --- |
| `reports/m0/M0_FINAL_ACCEPTANCE.md` | M0 | accepted | Read-only data engineering accepted. | no |
| `reports/m1/M1A_REVIEW_DECISION.md` | M1A | failed_validation | Trend leg failed validation and is not eligible for M2. | no |
| `reports/m1/M1F_FINAL_ACCEPTANCE.md` | M1F | accepted_as_feasibility_lab | Freqtrade Lab accepted only as research/backtest/WebUI candidate. | no |
| `reports/m1/M1B_FUNDING_ARBITRAGE_BACKTEST_REPORT.md` | M1B | failed_validation | M1B numerical funding-arbitrage validation failed because complete cycles 15 < 20. | no |
| `reports/m1/M1B_DECISION.md` | M1B | failed_validation | Records suitability conclusion B accepted and corrected numerical report failed validation. | no |
| `reports/m1/M1B_FREQTRADE_FUNDING_BACKTEST_SUITABILITY.md` | M1B | conclusion_b_accepted | Freqtrade is partial support only and external accounting is required. | no |
| `reports/m1/M1B_DATA_RUN_PROVENANCE.md` | M1B | public_data_provenance | Records local public-data run provenance and corrected time-indexed metrics methodology; no raw data, DuckDB, API keys, or private payloads are committed. | no |
| `reports/m1/M1B_FINAL_DECISION.md` | M1B | failed_validation | Final M1B decision; not eligible for M2. | no |
| `reports/m1/POST_M1B_REVIEW.md` | post-M1B | under_review | Reviews project after M1A and M1B failed validations. | no |
| `docs/decisions/ADR-0005-post-m1b-no-strategy-eligible-for-m2.md` | post-M1B | accepted | No strategy is eligible for M2. | no |

No report in this repository currently approves live trading, paper trading with real API, execution/live, order placement, or API trading permissions.
