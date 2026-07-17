from __future__ import annotations

import copy
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

from btc_eth_dual_quant.data.invalid_interval_quarantine import (
    ADR0015_FAULT_IDS,
    ActiveMembershipAuthority,
    InvalidIntervalPolicy,
    PolicyEvaluation,
    PolicyHardBlock,
    apply_invalid_interval_mask,
    assert_order_content_identity,
    build_invalid_interval_manifests,
    evaluate_invalid_interval_policy,
    read_verified_monthly_five_minute_archive,
)
from btc_eth_dual_quant.data.lifecycle_artifacts import make_v4_manifest
from btc_eth_dual_quant.data.liquid_universe import GridResult, MembershipRow, canonical_hash
import scripts.liquid_universe_v4_public_run as public_run
from scripts.liquid_universe_v4_public_run import (
    _apply_invalid_interval_artifact_overlay,
    _with_invalid_interval_mask,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config/liquid_spot_invalid_interval_policy_v1.json"
SOURCE_FREEZE = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"
MEMBERSHIP_HASH = "bcd93c0a4fdc7b1ca235ff8aa62722ecd38a6b990302886a3e91318763077ec5"
LIFECYCLE_HASH = "a78c52b183e0270c713dbb9965bd42b1035759b7b2182e49a3416cd8ae73904d"
OPEN_TIME = int(datetime(2030, 3, 4, 12, 0, tzinfo=timezone.utc).timestamp() * 1_000)
SYMBOLS = tuple(f"S{index:02d}USDT" for index in range(15))


def raw_row(open_time: int, close_time: int, *, volume: str = "10.0") -> str:
    return ",".join((
        str(open_time), "1.0", "2.0", "0.5", "1.5", volume,
        str(close_time), "15.0", "1", "5.0", "7.5", "0",
    ))


def membership_rows(symbols: tuple[str, ...] = SYMBOLS) -> list[dict]:
    return [
        {"effective_month": "2030-03-01", "symbol": symbol, "rank": index}
        for index, symbol in enumerate(symbols, 1)
    ]


def authority(*, endings: dict[str, int] | None = None, membership_hash: str = MEMBERSHIP_HASH) -> ActiveMembershipAuthority:
    return ActiveMembershipAuthority.build(
        membership_rows(),
        membership_manifest_content_hash=membership_hash,
        lifecycle_registry_hash=LIFECYCLE_HASH,
        lifecycle_end_exclusive_ms=endings,
    )


def write_archive(root: Path, symbol: str, rows: list[str], *, month: str = "2030-03") -> tuple[Path, dict]:
    path = root / "monthly" / "klines" / symbol / "5m" / f"{symbol}-5m-{month}.zip"
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{symbol}-5m-{month}.csv", "\n".join(rows) + "\n")
    payload = path.read_bytes()
    binding = {
        "canonical_key": f"data/spot/monthly/klines/{symbol}/5m/{symbol}-5m-{month}.zip",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "byte_size": len(payload),
    }
    return path, binding


def physical_rows(
    root: Path,
    invalid_count: int,
    *,
    symbols: tuple[str, ...] = SYMBOLS,
    open_time: int = OPEN_TIME,
    duplicate_symbol: str | None = None,
    bad_volume_symbol: str | None = None,
) -> tuple:
    output = []
    for index, symbol in enumerate(symbols):
        close_time = open_time + (299_000 if index < invalid_count else 299_999)
        row = raw_row(open_time, close_time, volume="nan" if symbol == bad_volume_symbol else "10.0")
        rows = [row, row] if symbol == duplicate_symbol else [row]
        path, binding = write_archive(root, symbol, rows)
        output.extend(read_verified_monthly_five_minute_archive(
            path,
            binding=binding,
            symbol=symbol,
            month="2030-03",
            source_freeze_content_hash=SOURCE_FREEZE,
        ))
    return tuple(output)


def physical_rows_for_times(root: Path, invalid_count: int, open_times: tuple[int, ...]) -> tuple:
    output = []
    for index, symbol in enumerate(SYMBOLS):
        rows = [
            raw_row(open_time, open_time + (299_000 if index < invalid_count else 299_999))
            for open_time in open_times
        ]
        path, binding = write_archive(root, symbol, rows)
        output.extend(read_verified_monthly_five_minute_archive(
            path,
            binding=binding,
            symbol=symbol,
            month="2030-03",
            source_freeze_content_hash=SOURCE_FREEZE,
        ))
    return tuple(output)


class InvalidIntervalPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = InvalidIntervalPolicy.from_path(POLICY_PATH)

    def evaluate(self, rows, *, membership=None, claims=()):
        return evaluate_invalid_interval_policy(
            rows,
            policy=self.policy,
            membership=membership or authority(),
            existing_policy_claims=claims,
        )

    def test_policy_is_hash_bound_and_authority_is_narrow(self) -> None:
        self.assertEqual(self.policy.minimum_count, 2)
        self.assertEqual((self.policy.fraction_numerator, self.policy.fraction_denominator), (4, 5))
        document = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        changed = copy.deepcopy(document)
        changed["authorizations"]["fixed_range_public_requalification"] = True
        with self.assertRaisesRegex(PolicyHardBlock, "canonical hash"):
            InvalidIntervalPolicy.from_document(changed)

    def test_fifteen_of_fifteen_and_twelve_of_fifteen_are_accepted(self) -> None:
        for invalid_count in (15, 12):
            with self.subTest(invalid_count=invalid_count), tempfile.TemporaryDirectory() as temporary:
                rows = physical_rows(Path(temporary), invalid_count)
                result = self.evaluate(rows)
                self.assertFalse(result.blockers)
                self.assertEqual(len(result.events), 1)
                self.assertEqual(result.events[0].invalid_count, invalid_count)
                self.assertEqual(len(result.masks), 15)

    def test_fourteen_of_fifteen_masks_the_valid_minority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            rows = physical_rows(Path(temporary), 14)
            result = self.evaluate(rows)
            event = result.events[0]
            self.assertEqual(event.valid_minority_members, (SYMBOLS[-1],))
            minority = next(item for item in result.masks if item.symbol == SYMBOLS[-1])
            self.assertEqual(minority.classification, "valid_minority")
            retained = apply_invalid_interval_mask(rows, result)
            self.assertEqual(retained, ())
            self.assertEqual(result.accounting["total_rows_quarantined"], 15)

    def test_fraction_and_minimum_count_fail_closed(self) -> None:
        for invalid_count, reason in ((11, "affected_fraction_below_threshold"), (1, "affected_symbol_count_below_threshold")):
            with self.subTest(invalid_count=invalid_count), tempfile.TemporaryDirectory() as temporary:
                result = self.evaluate(physical_rows(Path(temporary), invalid_count))
                self.assertFalse(result.events)
                self.assertEqual(result.blockers[0].reason, reason)

    def test_lifecycle_reduces_active_denominator_without_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            active = SYMBOLS[:-1]
            rows = physical_rows(Path(temporary), 12, symbols=active)
            result = self.evaluate(rows, membership=authority(endings={SYMBOLS[-1]: OPEN_TIME}))
            self.assertFalse(result.blockers)
            self.assertEqual(result.events[0].total_quarantined_count, 14)
            self.assertNotIn(SYMBOLS[-1], result.events[0].active_members)

    def test_input_order_and_generated_time_do_not_change_content_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            rows = physical_rows(Path(temporary), 14)
            reverse = tuple(reversed(rows))
            shuffled = list(rows)
            random.Random(12345).shuffle(shuffled)
            evaluations = [self.evaluate(value) for value in (rows, reverse, tuple(shuffled))]
            identity = assert_order_content_identity(evaluations)
            self.assertEqual(identity, evaluations[0].content_hash)
            first = build_invalid_interval_manifests(self.policy, authority(), evaluations[0], generated_utc="2030-01-01T00:00:00Z")
            second = build_invalid_interval_manifests(self.policy, authority(), evaluations[0], generated_utc="2040-01-01T00:00:00Z")
            self.assertEqual(
                {name: item["content_hash"] for name, item in first.items()},
                {name: item["content_hash"] for name, item in second.items()},
            )

    def test_public_grid_overlay_rebuilds_hour_and_day_after_two_same_hour_masks(self) -> None:
        second_open = OPEN_TIME + 300_000
        with tempfile.TemporaryDirectory() as temporary:
            rows = physical_rows_for_times(Path(temporary), 12, (OPEN_TIME, second_open))
            result = self.evaluate(rows)
            self.assertEqual(len(result.events), 2)
            self.assertEqual(apply_invalid_interval_mask(rows, result), ())
            missing = tuple(
                datetime.fromtimestamp(value / 1_000, timezone.utc)
                for value in (OPEN_TIME, second_open)
            )
            grid = _with_invalid_interval_mask(
                GridResult(SYMBOLS[0], "2030-03", 2, 0, missing, ()),
                {OPEN_TIME, second_open},
            )
            self.assertTrue(grid.complete)
            contents = {
                "expected_grid_manifest": [{
                    "symbol": SYMBOLS[0], "month": "2030-03", "expected_count": 2,
                    "actual_count": 0, "missing_count": 0, "errors": [], "complete": True,
                }],
                "complete_day_mask": {},
                "qualified_panel_manifest": [{
                    "effective_month": "2030-03", "symbol": SYMBOLS[0], "status": "clean",
                    "expected_1h_count": 744, "quarantined_1h_count": 0, "valid_1h_count": 744,
                }],
                "qualification_summary": {},
            }
            _apply_invalid_interval_artifact_overlay(contents, result)
            panel = contents["qualified_panel_manifest"][0]
            self.assertEqual(panel["invalid_interval_quarantined_1h_count"], 1)
            self.assertEqual(panel["valid_1h_count"], 743)
            self.assertEqual(contents["qualification_summary"]["invalid_interval_quarantined_days"], 1)

    def test_public_run_uses_only_temporary_synthetic_archives_and_outputs(self) -> None:
        fixture_month = "2026-06"
        fixture_open = int(datetime(2026, 6, 3, 12, 0, tzinfo=timezone.utc).timestamp() * 1_000)
        lifecycle_hash = canonical_hash({"fixture": "empty-lifecycle-registry"})
        v4_contract_hash = canonical_hash({"fixture": "v4-contract"})
        v3_contract_hash = canonical_hash({"fixture": "v3-contract"})
        row_registry_hash = canonical_hash({"fixture": "row-registry"})
        lifecycle_policy_hash = canonical_hash({"fixture": "lifecycle-policy"})
        eligibility_hash = canonical_hash({"fixture": "eligibility"})

        membership = [
            MembershipRow(
                effective_month=f"{fixture_month}-01",
                symbol=symbol,
                rank=index,
                median_daily_quote_volume_90d=str(1_000_000 - index),
                history_days=365,
                eligibility_status="eligible",
                exclusion_reason=None,
                ranking_window_start="2026-03-01",
                ranking_window_end_exclusive="2026-06-01",
                history_window_start="2025-06-01",
                history_window_end_exclusive="2026-06-01",
                contract_hash=v3_contract_hash,
                asset_registry_hash=eligibility_hash,
                input_provenance_hash=canonical_hash({"fixture-member": symbol}),
            )
            for index, symbol in enumerate(SYMBOLS, 1)
        ]
        membership_content = [asdict(row) for row in membership]
        membership_hash = make_v4_manifest(
            "membership_manifest",
            membership_content,
            contract_hash=v4_contract_hash,
            lifecycle_registry_hash=lifecycle_hash,
        )["content_hash"]
        source_freeze_hash = canonical_hash({"fixture": "synthetic-zip-source-freeze"})
        policy_document = copy.deepcopy(json.loads(POLICY_PATH.read_text(encoding="utf-8")))
        policy_document["bindings"]["membership_manifest_content_hash"] = membership_hash
        policy_document["bindings"]["lifecycle_registry_hash"] = lifecycle_hash
        policy_document["bindings"]["source_freeze_content_hash"] = source_freeze_hash
        policy_document["canonical_hash"] = canonical_hash({
            key: value for key, value in policy_document.items() if key != "canonical_hash"
        })
        fixture_policy = InvalidIntervalPolicy.from_document(policy_document)

        v3_contract = {
            "universe_id": "LIQUID-SPOT-USDT-TOP15-V3",
            "canonical_hash": v3_contract_hash,
        }
        v4_contract = {
            "universe_id": "LIQUID-SPOT-USDT-TOP15-V4",
            "canonical_hash": v4_contract_hash,
            "frozen_end_month": "2026-06",
            "research_start": "2020-01-01",
            "bindings": {
                "v3_contract_hash": v3_contract_hash,
                "v3_row_conflict_registry_hash": row_registry_hash,
                "lifecycle_policy_config_hash": lifecycle_policy_hash,
                "lifecycle_event_registry_hash": lifecycle_hash,
            },
        }
        fake_lifecycle = SimpleNamespace(events=(), canonical_hash=lifecycle_hash, document={"events": []})
        fake_row_registry = SimpleNamespace(entries=(), canonical_hash=row_registry_hash)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw_root = root / "synthetic-raw"
            evidence_dir = root / "synthetic-evidence"
            source_bindings = {}
            for index, symbol in enumerate(SYMBOLS):
                close_delta = 299_000 if index < 12 else 299_999
                _, binding = write_archive(
                    raw_root,
                    symbol,
                    [raw_row(fixture_open, fixture_open + close_delta)],
                    month=fixture_month,
                )
                source_bindings[binding["canonical_key"]] = binding

            def fake_load(name: str):
                values = {
                    "config/liquid_spot_universe_contract_v4.json": v4_contract,
                    "config/liquid_spot_lifecycle_policy_v4.json": {"canonical_hash": lifecycle_policy_hash},
                    "config/liquid_spot_universe_contract_v3.json": v3_contract,
                    "config/liquid_spot_asset_eligibility_v2.json": {"canonical_hash": eligibility_hash},
                    "config/liquid_spot_confirmed_archive_gaps_v2.json": {},
                    "reports/m0/evidence/liquid_universe_v3/membership_manifest.json": {"content": membership_content},
                    "reports/m0/evidence/liquid_universe_v3/qualification_summary.json": {"content": {"status": "blocked"}},
                }
                return copy.deepcopy(values[name])

            def fake_v3_artifacts(**kwargs):
                panel = [
                    {
                        "effective_month": fixture_month,
                        "symbol": symbol,
                        "status": "synthetic_fixture",
                        "expected_1h_count": 720,
                        "quarantined_1h_count": 0,
                        "valid_1h_count": 720,
                    }
                    for symbol in SYMBOLS
                ]
                summary = {
                    "status": "blocked",
                    "end_month": "2026-06",
                    "expected_months": 1,
                    "membership_rows": 15,
                    "unresolved_row_conflicts": 0,
                    "unresolved_gaps": 0,
                    "processing_errors": 0,
                    "excluded_category_members": 0,
                    "synthetic_fills": 0,
                    "replacement_members": 0,
                    "blockers": ["synthetic_fixture_incomplete_month"],
                }
                return {
                    "source_manifest": {"content": kwargs["source_rows"]},
                    "conflict_resolution_manifest": {"content": []},
                    "candidate_eligibility_manifest": {"content": []},
                    "membership_manifest": {"content": membership_content},
                    "qualified_panel_manifest": {"content": panel},
                    "qualification_summary": {"content": summary},
                }

            with (
                mock.patch.object(public_run, "_load", side_effect=fake_load),
                mock.patch.object(public_run, "_frozen_source_bindings", return_value=source_bindings),
                mock.patch.object(public_run.InvalidIntervalPolicy, "from_path", return_value=fixture_policy),
                mock.patch.object(public_run.LifecycleEventRegistry, "from_path", return_value=fake_lifecycle),
                mock.patch.object(public_run.ResolutionRegistry, "from_path", return_value=fake_row_registry),
                mock.patch.object(public_run, "ensure_registered_archives"),
                mock.patch.object(public_run, "_collect_daily_sources", return_value=({}, {}, [], [])),
                mock.patch.object(public_run, "build_daily_v4", return_value=([], [], [], [])),
                mock.patch.object(public_run, "build_membership_rows", return_value=membership),
                mock.patch.object(public_run, "build_artifacts_v3", side_effect=fake_v3_artifacts),
                mock.patch.object(
                    public_run,
                    "read_verified_monthly_five_minute_archive",
                    wraps=read_verified_monthly_five_minute_archive,
                ) as read_archives,
                mock.patch.object(public_run, "write_manifest", wraps=public_run.write_manifest) as write_manifests,
            ):
                artifacts = public_run.run(
                    raw_root=raw_root,
                    evidence_dir=evidence_dir,
                    end_month="2026-06",
                    report_path=root / "qualification.md",
                    diff_report_path=root / "diff.md",
                    offline=True,
                    workers=1,
                    verify_remote_registry=False,
                )

            self.assertEqual(artifacts["invalid_interval_accounting_manifest"]["content"]["event_count"], 1)
            self.assertEqual(artifacts["invalid_interval_accounting_manifest"]["content"]["total_rows_quarantined"], 15)
            self.assertEqual(len(artifacts["invalid_interval_slot_mask_manifest"]["content"]), 15)
            self.assertTrue(all(
                Path(call.args[0]).is_relative_to(raw_root)
                for call in read_archives.call_args_list
            ))
            self.assertTrue(all(
                Path(call.args[0]).is_relative_to(evidence_dir)
                for call in write_manifests.call_args_list
            ))
            self.assertFalse((public_run.DEFAULT_EVIDENCE / "invalid_interval_event_manifest.json").exists())
            self.assertEqual(
                {path.name for path in evidence_dir.glob("invalid_interval_*.json")},
                {f"{name}.json" for name in (
                    "invalid_interval_policy_manifest",
                    "invalid_interval_event_manifest",
                    "invalid_interval_slot_mask_manifest",
                    "invalid_interval_accounting_manifest",
                )},
            )

    def test_archive_and_raw_row_tampering_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path, binding = write_archive(root, SYMBOLS[0], [raw_row(OPEN_TIME, OPEN_TIME + 299_000)])
            changed = dict(binding, byte_size=binding["byte_size"] + 1)
            with self.assertRaisesRegex(PolicyHardBlock, "archive_or_evidence_hash_drift"):
                read_verified_monthly_five_minute_archive(
                    path, binding=changed, symbol=SYMBOLS[0], month="2030-03",
                    source_freeze_content_hash=SOURCE_FREEZE,
                )
            row = read_verified_monthly_five_minute_archive(
                path, binding=binding, symbol=SYMBOLS[0], month="2030-03",
                source_freeze_content_hash=SOURCE_FREEZE,
            )[0]
            repaired = replace(row, close_time_ms=OPEN_TIME + 299_999)
            self.assertIn("raw_timestamp_repaired", repaired.identity_errors())

    def test_all_sixteen_reviewed_fault_ids_have_executable_hard_blocks(self) -> None:
        outcomes: dict[str, str] = {}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            off_grid = physical_rows(root / "off", 12, open_time=OPEN_TIME + 1)
            outcomes["ADR0015-FI-001"] = self.evaluate(off_grid).blockers[0].reason
            bad = physical_rows(root / "bad", 12, bad_volume_symbol=SYMBOLS[0])
            outcomes["ADR0015-FI-002"] = self.evaluate(bad).blockers[0].reason
            duplicate = physical_rows(root / "dup", 12, duplicate_symbol=SYMBOLS[0])
            outcomes["ADR0015-FI-003"] = self.evaluate(duplicate).blockers[0].reason
            missing = physical_rows(root / "missing", 12, symbols=SYMBOLS[:-1])
            outcomes["ADR0015-FI-004"] = self.evaluate(missing).blockers[0].reason
            nonmember_symbols = SYMBOLS + ("OUTSIDEUSDT",)
            nonmember = physical_rows(root / "outside", 16, symbols=nonmember_symbols)
            outcomes["ADR0015-FI-005"] = self.evaluate(nonmember).blockers[0].reason
            outcomes["ADR0015-FI-006"] = self.evaluate(physical_rows(root / "fraction", 11)).blockers[0].reason
            outcomes["ADR0015-FI-007"] = self.evaluate(physical_rows(root / "single", 1)).blockers[0].reason

            path, binding = write_archive(root / "drift", SYMBOLS[0], [raw_row(OPEN_TIME, OPEN_TIME + 299_000)])
            try:
                read_verified_monthly_five_minute_archive(
                    path, binding={**binding, "sha256": "0" * 64}, symbol=SYMBOLS[0], month="2030-03",
                    source_freeze_content_hash=SOURCE_FREEZE,
                )
            except PolicyHardBlock as exc:
                outcomes["ADR0015-FI-008"] = str(exc)
            try:
                self.evaluate(physical_rows(root / "membership", 12), membership=authority(membership_hash="0" * 64))
            except PolicyHardBlock as exc:
                outcomes["ADR0015-FI-009"] = str(exc)

            complete_rows = physical_rows(root / "mask", 14)
            complete = self.evaluate(complete_rows)
            partial = PolicyEvaluation(complete.events, complete.masks[:-1], complete.blockers, complete.accounting)
            try:
                apply_invalid_interval_mask(complete_rows, partial)
            except PolicyHardBlock as exc:
                outcomes["ADR0015-FI-010"] = str(exc)
            repaired = replace(complete_rows[0], close_time_ms=complete_rows[0].open_time_ms + 299_999)
            outcomes["ADR0015-FI-011"] = repaired.identity_errors()[0]

            base = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
            for fault_id, key in (("ADR0015-FI-012", "synthetic_fills"), ("ADR0015-FI-013", "replacement_members"), ("ADR0015-FI-014", "known_date_symbol_or_row_exceptions")):
                changed = copy.deepcopy(base)
                changed["algorithm"][key] = True
                try:
                    InvalidIntervalPolicy.from_document(changed)
                except PolicyHardBlock as exc:
                    outcomes[fault_id] = str(exc)
            overlap = self.evaluate(physical_rows(root / "overlap", 12), claims={(SYMBOLS[0], OPEN_TIME)})
            outcomes["ADR0015-FI-015"] = overlap.blockers[0].reason
            try:
                assert_order_content_identity((complete, PolicyEvaluation((), (), (), {"changed": True})))
            except PolicyHardBlock as exc:
                outcomes["ADR0015-FI-016"] = str(exc)

        self.assertEqual(set(outcomes), set(ADR0015_FAULT_IDS))
        self.assertTrue(all(outcomes.values()))


if __name__ == "__main__":
    unittest.main()
