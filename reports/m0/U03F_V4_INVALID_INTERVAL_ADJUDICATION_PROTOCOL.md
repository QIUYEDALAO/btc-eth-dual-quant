# U-03F V4 Invalid-Interval Adjudication Protocol

- Status: frozen_before_diagnostic_run
- Starting main: `3ba411d28563526a5357e3882a1e5759311f6179`
- Input repair requalification: PR #100 / blocked / 119 processing errors
- Source mode: frozen_local_only
- Source archives: 27,736
- Source freeze: `c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c`
- Protocol content hash: `9589510619bcda09041dba40abdf25fed38b5b12044892bd315e08e84e862190`
- Diagnostic run executed: no
- Production pipeline modified: no
- Policy adopted: no
- Public requalification executed: no
- New independent audit executed: no
- U-04 authorized: no
- Strategy/OOS/API/trading/M2 authorized: no

## Frozen Diagnostic Gate

The future diagnostic must verify each archive binding and ZIP CRC before using
integer-only timestamp parsing. A valid 5m row requires a grid-aligned open and
an exact 299,999ms close delta. Every invalid physical row must retain its exact
archive, line-number and raw-row hash provenance.

Rows are grouped only by exact open time and compared against the frozen monthly
membership. The existing synchronous threshold remains 2 symbols and 80%, but
meeting it is diagnostic evidence only. It cannot directly authorize reuse of
the existing gap policy or a per-row exception registry.

Normal, reverse and deterministic-shuffled runs must produce identical canonical
content hashes. Any source/hash drift, missing or duplicated expected row,
unexpected or non-member row, traversal mismatch, policy preselection or
authorization expansion fails closed.

## Allowed Next Result

After this protocol merges, one evidence-only diagnostic may run. Its allowed
decisions are `new_policy_adr_required`, `official_source_followup_required` or
`blocked_evidence_mismatch`. A successful synchronization finding authorizes at
most a separate Draft policy ADR after the diagnostic evidence merges.

Runtime implementation, requalification, a new independent audit and U-04 all
remain unauthorized.
