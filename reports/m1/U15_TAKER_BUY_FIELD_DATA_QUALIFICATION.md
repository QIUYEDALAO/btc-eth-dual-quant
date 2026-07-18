# U-15 Taker-Buy Field/Data Qualification

- Status: `failed_pre_result_field_qualification`
- Candidate: `U15-CROSS-SECTIONAL-TAKER-BUY-ABSORPTION-PERSISTENCE`
- Result hash: `83eb8ac2ec1726884f9b3f37bcfe0c13620bca06e98e7539a0e79466d8d63c28`

The qualification stopped at the first official-field Gate failure, before any
taker state, candidate, event, path, return or OOS value was generated.

`ADAUSDT` at `2020-01-01T00:05:00Z` is a checksum-bound official 5m row with
12 columns, zero trades, zero quote volume and zero taker-buy base/quote
volume. The frozen protocol requires quote volume to be strictly positive for
every consumed row and expressly forbids inference, repair, fill or cross-field
substitution. The row therefore fails the protocol exactly as written.

The scan did not continue to count or characterize later failures. Reverse and
shuffled field traversals, structural preflight and synthetic complexity were
not run after the fail-closed stop. U-15 is closed before Paper observation;
its thresholds and field contract are not changed, and OOS remains sealed.
