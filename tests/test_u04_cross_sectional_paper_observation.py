from __future__ import annotations

import copy
import json
import tempfile
import unittest
import zipfile
from decimal import Decimal, localcontext
from pathlib import Path

from scripts.u04_cross_sectional_paper_observation import (
    FIVE_MINUTES_MS,
    ONE_HOUR_MS,
    cluster_events,
    evaluate_gates,
    identity_hash,
    observe_paths,
    read_five_minute_rows,
    select_events,
)
from scripts.u04_cross_sectional_paper_observation_check import (
    EVIDENCE,
    EXPECTED_HASHES,
    REPORT,
    validate as validate_result,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads((ROOT / "config/u04_cross_sectional_paper_protocol_v1.json").read_text())


class U04CrossSectionalPaperObservationTests(unittest.TestCase):
    def test_residual_event_uses_completed_cross_section_and_tie_break(self):
        symbols = tuple(f"S{index:02d}USDT" for index in range(15))
        start = 1577836800000
        decision = start + 2 * ONE_HOUR_MS
        closes = {}
        with localcontext() as context:
            context.prec = 50
            background = (Decimal("-0.006"), Decimal("-0.005"), Decimal("-0.004"), Decimal("-0.003"), Decimal("-0.002"), Decimal("-0.001"), Decimal("0"), Decimal("0.001"), Decimal("0.002"), Decimal("0.003"), Decimal("0.004"), Decimal("0.005"), Decimal("0.006"))
            for index, symbol in enumerate(symbols):
                member_return = Decimal("-0.05") if index < 2 else background[index - 2]
                closes[symbol] = {
                    decision - ONE_HOUR_MS: Decimal(100),
                    decision: Decimal(100) * member_return.exp(),
                }
        events, accounting = select_events(
            hourly_closes=closes,
            membership={"2020-01": symbols},
            is_start_ms=start,
            is_end_ms=decision + ONE_HOUR_MS,
            protocol_hash="a" * 64,
            qualification_hash="b" * 64,
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["symbol"], symbols[0])
        self.assertEqual(accounting["simultaneous_candidates_discarded"], 1)

    def test_missing_member_and_zero_mad_are_ineligible(self):
        symbols = tuple(f"S{index:02d}USDT" for index in range(15))
        start = 1577836800000
        decision = start + 2 * ONE_HOUR_MS
        closes = {symbol: {decision - ONE_HOUR_MS: Decimal(100), decision: Decimal(100)} for symbol in symbols}
        _, accounting = select_events(
            hourly_closes=closes, membership={"2020-01": symbols}, is_start_ms=start,
            is_end_ms=decision, protocol_hash="a" * 64, qualification_hash="b" * 64,
        )
        self.assertEqual(accounting["scale_ineligible"], 1)
        del closes[symbols[-1]][decision]
        _, accounting = select_events(
            hourly_closes=closes, membership={"2020-01": symbols}, is_start_ms=start,
            is_end_ms=decision, protocol_hash="a" * 64, qualification_hash="b" * 64,
        )
        self.assertEqual(accounting["cross_section_ineligible"], 2)

    def test_connected_24h_cluster_keeps_first_and_chains(self):
        base = 1577836800000
        events = [
            {"decision_time_ms": base + offset * ONE_HOUR_MS, "symbol": "A", "event_id": str(offset)}
            for offset in (0, 24, 48, 73)
        ]
        episodes = cluster_events(events)
        self.assertEqual([row["event_id"] for row in episodes], ["0", "73"])

    def test_path_diagnostics_use_next_open_and_peer_median(self):
        reference = 1577836800000
        symbols = ["A", *[f"P{index}" for index in range(14)]]
        episode = {"episode_id": "e", "event_id": "x", "decision_time_ms": reference - 1, "reference_open_time_ms": reference, "symbol": "A", "active_members": symbols}
        captured = {}
        for index in range(288):
            opened = reference + index * FIVE_MINUTES_MS
            candidate_close = Decimal(100) + Decimal(index + 1) / Decimal(144)
            captured[("A", opened)] = (Decimal(100), candidate_close, Decimal(99), candidate_close)
            for peer in symbols[1:]:
                captured[(peer, opened)] = (Decimal(100), Decimal(100), Decimal(100), Decimal(100))
        paths, censored = observe_paths([episode], captured, {})
        self.assertEqual(censored, {})
        self.assertEqual(len(paths), 1)
        self.assertEqual(Decimal(paths[0]["absolute_close_displacement"]["24"]), Decimal("0.02"))
        self.assertGreater(Decimal(paths[0]["relative_peer_median_recovery"]["24"]), Decimal("0.019"))
        self.assertEqual(paths[0]["first_recovery_minutes"], 5)

    def test_missing_peer_right_censors_without_search(self):
        reference = 1577836800000
        episode = {"episode_id": "e", "event_id": "x", "decision_time_ms": reference - 1, "reference_open_time_ms": reference, "symbol": "A", "active_members": ["A", "B"]}
        captured = {}
        for index in range(288):
            opened = reference + index * FIVE_MINUTES_MS
            captured[("A", opened)] = (Decimal(100), Decimal(100), Decimal(100), Decimal(100))
            if index != 4:
                captured[("B", opened)] = (Decimal(100), Decimal(100), Decimal(100), Decimal(100))
        paths, censored = observe_paths([episode], captured, {})
        self.assertEqual(paths, [])
        self.assertEqual(censored["missing_or_quarantined_5m"], 1)

    def test_reader_stops_before_oos_ohlc_decode(self):
        start = 1577836800000
        boundary = start + FIVE_MINUTES_MS
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data/spot/monthly/klines/AAAUSDT/5m/AAAUSDT-5m-2020-01.zip"
            path.parent.mkdir(parents=True)
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(
                    "AAAUSDT-5m-2020-01.csv",
                    f"{start},1,1,1,1,1,{start+FIVE_MINUTES_MS-1},1,1,1,1,0\n{boundary},NOT_DECODED\n",
                )
            rows = list(read_five_minute_rows(root, "AAAUSDT", "2020-01", is_start_ms=start, is_end_ms=boundary))
            self.assertEqual(len(rows), 1)

    def test_frozen_gates_pass_and_fail_without_mutation(self):
        paths = []
        start = 1577836800000
        symbols = [f"S{index}" for index in range(9)]
        for index in range(90):
            year_offset = (index % 3) * 366 * 24 * ONE_HOUR_MS
            paths.append({
                "decision_time_ms": start + year_offset + index * 25 * ONE_HOUR_MS,
                "symbol": symbols[index % len(symbols)],
                "relative_peer_median_recovery": {"24": "0.020"},
                "absolute_close_displacement": {"24": "0.020"},
            })
        _, checks = evaluate_gates(paths, PROTOCOL, mismatch_count=0)
        self.assertTrue(all(checks.values()))
        _, failed = evaluate_gates(paths, PROTOCOL, mismatch_count=1)
        self.assertFalse(failed["authority_and_order_mismatches"])

    def test_protocol_hash_and_thresholds_are_not_modified(self):
        frozen = copy.deepcopy(PROTOCOL)
        self.assertEqual(frozen["content_hash"], "7b0e462dd9d4f51de1419005bb8701b859f4d2be6148121c1e68cdd0089629d6")
        self.assertEqual(frozen["residual_event"]["standardized_residual_maximum"], "-3.0")
        self.assertEqual(frozen["residual_event"]["relative_simple_return_maximum"], "-0.0180")
        self.assertFalse(frozen["observation_contract"]["formal_strategy_return"])

    def test_committed_failed_result_is_exact(self):
        summary = json.loads((EVIDENCE / "run_manifest.json").read_text())
        manifests = {name: json.loads((EVIDENCE / f"{name}.json").read_text()) for name in EXPECTED_HASHES}
        self.assertEqual(validate_result(summary, manifests, REPORT.read_text(encoding="utf-8")), [])

    def test_result_tamper_cannot_turn_failure_into_pass(self):
        summary = json.loads((EVIDENCE / "run_manifest.json").read_text())
        manifests = {name: json.loads((EVIDENCE / f"{name}.json").read_text()) for name in EXPECTED_HASHES}
        for field, value in (
            ("status", "pass"), ("oos_opened", True), ("second_run_executed", True),
        ):
            changed = copy.deepcopy(summary)
            changed[field] = value
            changed["run_content_hash"] = identity_hash({key: item for key, item in changed.items() if key != "run_content_hash"})
            self.assertTrue(validate_result(changed, manifests, REPORT.read_text(encoding="utf-8")), field)


if __name__ == "__main__":
    unittest.main()
