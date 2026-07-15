from __future__ import annotations

import unittest

from btc_eth_dual_quant.data.kline_row_conflicts import (
    RawKlineRow,
    classify_complete_group,
    normalize_kline_fields,
    structural_errors,
)


BASE = [
    "1548892800000", "1.0", "3.0", "0.5", "2.0", "10.0",
    "1548979199999", "20.0", "7", "4.0", "8.0", "0",
]


def raw(fields: list[str] | None = None, *, line: int = 1) -> RawKlineRow:
    return RawKlineRow.from_fields(
        symbol="FIXUSDT",
        interval="1d",
        fields=fields or BASE,
        line_number=line,
        archive_key="data/spot/monthly/klines/FIXUSDT/1d/FIXUSDT-1d-2019-01.zip",
        archive_sha256="a" * 64,
        authority="official_monthly_zip",
    )


class CompleteGroupPolicyTests(unittest.TestCase):
    def test_partial_daily_bar_is_valid_but_interval_overrun_is_not(self):
        fields = [
            "1775001600000000", "1", "2", "0.5", "1.5", "10",
            "1775012399999000", "15", "2", "5", "7", "0",
        ]
        self.assertEqual(structural_errors(fields, interval="1d"), ())
        fields[6] = "1775088000000000"
        self.assertIn("close_time outside interval", structural_errors(fields, interval="1d"))

    def test_exact_two_and_n_row_groups_are_collapsible(self):
        two = classify_complete_group([raw(line=1), raw(line=2)])
        many = classify_complete_group([raw(line=index) for index in range(1, 6)])
        self.assertEqual(two.classification, "byte_identical_duplicate")
        self.assertEqual(two.raw_multiplicity, 2)
        self.assertTrue(two.collapsible)
        self.assertEqual(many.raw_multiplicity, 5)
        self.assertEqual(len(many.raw_row_hashes), 5)

    def test_two_identical_plus_one_conflicting_blocks_entire_key(self):
        changed = BASE.copy()
        changed[4] = "2.1"
        group = classify_complete_group([raw(line=1), raw(line=2), raw(changed, line=3)])
        self.assertEqual(group.classification, "conflicting_duplicate")
        self.assertFalse(group.collapsible)
        self.assertEqual(group.raw_multiplicity, 3)

    def test_semantic_identical_and_parser_created_groups_block(self):
        formatted = BASE.copy()
        formatted[1] = "1.00"
        semantic = classify_complete_group([raw(line=1), raw(formatted, line=2)])
        self.assertEqual(semantic.classification, "semantic_identical_duplicate")
        self.assertFalse(semantic.collapsible)

        micros = BASE.copy()
        micros[0] = "1548892800000000"
        micros[6] = "1548979199999999"
        parser_created = classify_complete_group([raw(line=1), raw(micros, line=2)])
        self.assertEqual(parser_created.classification, "parser_created_duplicate")
        self.assertFalse(parser_created.collapsible)

    def test_canonical_semantics_cover_all_twelve_fields(self):
        normalized = normalize_kline_fields(BASE)
        self.assertEqual(len(normalized), 12)
        changed_ignore = BASE.copy()
        changed_ignore[11] = "1"
        self.assertNotEqual(normalized, normalize_kline_fields(changed_ignore))


if __name__ == "__main__":
    unittest.main()
