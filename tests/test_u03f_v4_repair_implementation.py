from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
import tempfile
import unittest
import zipfile

from btc_eth_dual_quant.audit.liquid_universe_v4_audit_artifacts import scan_float_timestamp_paths
from btc_eth_dual_quant.data.kline_row_conflicts import timestamp_ms
from scripts.liquid_universe_v4_public_run import _valid_five_minute_rows
from scripts.liquid_universe_v4_requalification import (
    _atomic_write_bytes,
    render_bound_report,
    verify_report_binding,
)


ROOT = Path(__file__).resolve().parents[1]


def kline(open_ms: int, *, close_ms: int | None = None) -> str:
    close = open_ms + 299_999 if close_ms is None else close_ms
    return f"{open_ms},1,1,1,1,1,{close},1,1,1,1,0\n"


def archive(path: Path, rows: list[str], *, symbol: str = "ADAUSDT", month: str = "2020-02") -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        handle.writestr(f"{symbol}-5m-{month}.csv", "".join(rows))


class U03FV4RepairImplementationTests(unittest.TestCase):
    def test_ft_int_precision_retains_integer_millisecond_identity(self) -> None:
        microseconds = "9007199254740999"
        self.assertEqual(timestamp_ms(microseconds), 9_007_199_254_740)
        self.assertNotEqual(timestamp_ms(microseconds), int(float(microseconds) / 1_000))

    def test_ft_static_float_path_fails_closed_on_reintroduction(self) -> None:
        paths = (
            ROOT / "src/btc_eth_dual_quant/data/liquid_universe_pipeline_v4.py",
            ROOT / "scripts/liquid_universe_v4_public_run.py",
        )
        for path in paths:
            self.assertEqual(scan_float_timestamp_paths(path.read_text(encoding="utf-8")), [])
        self.assertTrue(scan_float_timestamp_paths("value = instant.timestamp() * 1_000"))

    def test_ft_ada_invalid_interval_counts_8269_valid_physical_rows(self) -> None:
        start = 1_580_515_200_000
        rows = [kline(start + index * 300_000) for index in range(8_270)]
        invalid_open = start + 4_000 * 300_000
        rows[4_000] = kline(invalid_open, close_ms=invalid_open + 300_000)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ADAUSDT-5m-2020-02.zip"
            archive(path, rows)
            bars, errors = _valid_five_minute_rows(path, "ADAUSDT", "2020-02")
        self.assertEqual(len(bars), 8_269)
        self.assertEqual(errors, ["5m interval boundary is invalid"])
        self.assertNotIn("ADAUSDT", inspect.getsource(_valid_five_minute_rows))

    def test_ft_invalid_close_boundary_is_excluded_and_reported(self) -> None:
        opened = 1_580_515_200_000
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SOLUSDT-5m-2020-02.zip"
            archive(path, [kline(opened, close_ms=opened + 299_998)], symbol="SOLUSDT")
            bars, errors = _valid_five_minute_rows(path, "SOLUSDT", "2020-02")
        self.assertEqual(bars, [])
        self.assertEqual(errors, ["5m interval boundary is invalid"])

    def test_malformed_first_record_is_not_silently_treated_as_a_header(self) -> None:
        opened = 1_580_515_200_000
        malformed = "open_time,open,high,low,close,volume,close_time,quote,trades,taker_base,taker_quote,ignore\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SOLUSDT-5m-2020-02.zip"
            archive(path, [malformed, kline(opened)], symbol="SOLUSDT")
            bars, errors = _valid_five_minute_rows(path, "SOLUSDT", "2020-02")
        self.assertEqual(len(bars), 1)
        self.assertEqual(errors, ["kline timestamp must be an unsigned integer"])

    def test_ft_run_manifest_binds_exact_final_report_bytes(self) -> None:
        records = {"cold": {"artifact_set_hash": "a" * 64}}
        payload = render_bound_report(
            b"# report\n",
            records,
            source_freeze_hash="b" * 64,
            determinism_status="pass",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            _atomic_write_bytes(path, payload)
            digest = hashlib.sha256(payload).hexdigest()
            manifest = {"content": {"builds": {"cold": {"qualification_report_sha256": digest}}}}
            self.assertEqual(verify_report_binding(path, manifest), digest)

    def test_ft_report_byte_drift_invalidates_manifest_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            _atomic_write_bytes(path, b"frozen report\n")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest = {"content": {"builds": {"cold": {"qualification_report_sha256": digest}}}}
            path.write_bytes(path.read_bytes() + b"drift")
            with self.assertRaisesRegex(ValueError, "report binding mismatch"):
                verify_report_binding(path, manifest)


if __name__ == "__main__":
    unittest.main()
