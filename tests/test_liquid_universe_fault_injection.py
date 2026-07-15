from datetime import datetime, timezone
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from btc_eth_dual_quant.data.public_archive import atomic_store_verified_zip, ensure_archive, fetch_bytes_with_retry, verify_zip
from scripts.liquid_universe_public_run import _fetch_checksum_text


def valid_zip() -> bytes:
    buffer = io.BytesIO()
    row = "1704067200000,1,2,0.5,1.5,10,1704067499999,15,1,5,7,0\n"
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("BTCUSDT-5m-2024-01.csv", row)
    return buffer.getvalue()


class Response:
    def __init__(self, data: bytes): self.data = data
    def read(self): return self.data


class LiquidUniverseFaultInjectionTests(unittest.TestCase):
    def test_missing_partial_and_corrupt_zip_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "a.zip"
            with self.assertRaises(ValueError): verify_zip(path)
            path.write_bytes(b"PK")
            with self.assertRaises(ValueError): verify_zip(path)
            path.write_bytes(b"not-a-zip")
            with self.assertRaises(ValueError): verify_zip(path)

    def test_checksum_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "a.zip"
            path.write_bytes(valid_zip())
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                verify_zip(path, expected_sha256="0" * 64)

    def test_warm_cache_corruption_is_replaced(self):
        data = valid_zip()
        digest = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "a.zip"
            path.write_bytes(b"corrupt")
            result = ensure_archive(url="https://example/a.zip", destination=path, checksum_text=f"{digest} a.zip", opener=lambda *_args, **_kwargs: Response(data), sleep=lambda _delay: None)
            self.assertEqual(result[0], digest)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_retry_exhaustion_is_bounded(self):
        attempts = []
        def fail(*_args, **_kwargs):
            attempts.append(1)
            raise OSError("offline")
        with self.assertRaises(OSError):
            fetch_bytes_with_retry("https://example/a.zip", retries=3, opener=fail, sleep=lambda _delay: None)
        self.assertEqual(len(attempts), 3)

    def test_checksum_connection_reset_retries_and_recovers(self):
        attempts = []
        def flaky(*_args, **_kwargs):
            attempts.append(1)
            if len(attempts) < 3:
                raise ConnectionResetError("reset")
            return Response(b"a" * 64 + b"  archive.zip")
        text = _fetch_checksum_text("https://example/archive.zip.CHECKSUM", opener=flaky, sleep=lambda _delay: None)
        self.assertEqual(text, "a" * 64 + "  archive.zip")
        self.assertEqual(len(attempts), 3)

    def test_atomic_replace_interruption_preserves_existing_file(self):
        data = valid_zip()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "a.zip"
            path.write_bytes(b"old")
            def interrupted(_source, _destination): raise OSError("interrupted")
            with self.assertRaises(OSError):
                atomic_store_verified_zip(data, path, replace=interrupted)
            self.assertEqual(path.read_bytes(), b"old")
            self.assertEqual(list(path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
