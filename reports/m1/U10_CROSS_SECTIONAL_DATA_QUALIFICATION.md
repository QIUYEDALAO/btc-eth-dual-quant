# U-10 Frozen-Source Data Qualification

- Status: `pass`
- Contract: `c47701dca14ffab10b94efe2a855dd85c68ab01647c2feede3b8db86c80661bf`
- Result: `0029def278eeadf6b3951e1e1f62d16b0919889950eb68e0cdd3fe97fe727ee2`

All 27,736 frozen ZIP identities, 19 V4 manifests and complete 5m-derived daily
price/quote-volume authority pass in three orders. Calendar and membership-only
preflight independently derives 1,603 eligible constant-membership decision days
and a maximum 418 independent 72h episodes, above protocol minimum 400 and
Paper Gate 90.

The run decoded zero OOS OHLCV values and generated zero daily signal,
candidate, event, path or return rows. Exactly one sealed-IS Paper observation
is authorized; no second result-bearing run or parameter change is allowed.
