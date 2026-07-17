# ADR-0015 Invalid-Interval Policy Draft

- Status: proposed_draft_non_authoritative
- Policy adopted: no
- Implementation authorized: no
- Production pipeline modified: no
- Public requalification authorized: no
- New independent audit authorized: no
- U-04 authorized: no
- M2 authorized: no

## Bound Evidence

This Draft binds PR #102's protocol content hash
`9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190`
and PR #103's diagnostic content/run hashes
`ae5ae831a7a5805cbf0265bc2f9ba34017b79224112eea68bedffa60bac5c677`
and `df401c071038462b6311193d106fd8b0034f5c5f06f756d0daf821564233dd33`.
The evidence remains 119 exact rows in eight synchronous windows from three
content-identical traversals of 27,736 frozen archives.

## Draft Result

The proposed generic rule requires at least two invalid active members and an
invalid-active fraction of at least 0.80 at one grid-aligned 5m open time. Its
sole eligible defect is a close-time boundary mismatch after every other
strict physical-row and source-integrity check passes. A future accepted event
would quarantine the complete active-member slot, including valid minority
rows, while leaving all raw evidence byte-immutable.

No known date or symbol is a runtime input. No row is repaired, replaced,
filled or deleted. The V2 gap-policy contract is reference-only and is not
silently reused as authority for this defect class.

## Gate

The only successor after this Draft merges is an independent review of its
exact head. Any mismatch, critical finding or high finding fails closed.
Review approval alone does not adopt the policy. Implementation, requalification, a
new audit and U-04 all remain unauthorized.
