"""Verified, atomic access to Binance public ZIP archives."""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
import tempfile
import time
from typing import Callable
import urllib.error
import urllib.request
import zipfile

from btc_eth_dual_quant.data.liquid_universe import canonical_hash


@dataclass(frozen=True)
class SourceManifestRow:
    canonical_key: str
    canonical_url: str
    symbol: str
    interval: str
    archive_month: str
    byte_size: int
    sha256: str
    verification_status: str
    row_count: int
    first_timestamp: str
    last_timestamp: str
    authority_role: str

    def content_id(self) -> str:
        return canonical_hash(asdict(self))


def _archive_timestamp(value: str) -> datetime:
    raw = int(value)
    divisor = 1_000_000 if raw >= 10**15 else 1_000
    return datetime.fromtimestamp(raw / divisor, timezone.utc)


def parse_checksum(text: str) -> str:
    token = text.strip().split()[0].lower() if text.strip() else ""
    if len(token) != 64 or any(char not in "0123456789abcdef" for char in token):
        raise ValueError("invalid checksum document")
    return token


def verify_zip(path: Path, *, expected_sha256: str | None = None) -> tuple[str, int, str, str]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("archive file missing or empty")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256.lower():
        raise ValueError("archive checksum mismatch")
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad is not None:
                raise ValueError(f"archive CRC failure: {bad}")
            names = [name for name in archive.namelist() if name.endswith(".csv")]
            if len(names) != 1:
                raise ValueError("archive must contain exactly one CSV")
            first = last = ""
            count = 0
            with archive.open(names[0]) as handle:
                for row in csv.reader(io.TextIOWrapper(handle, encoding="utf-8")):
                    if not row or not row[0].isdigit():
                        continue
                    timestamp = _archive_timestamp(row[0]).isoformat()
                    first = first or timestamp
                    last = timestamp
                    count += 1
            if count == 0:
                raise ValueError("archive contains no data rows")
    except zipfile.BadZipFile as exc:
        raise ValueError("corrupt ZIP archive") from exc
    return digest, count, first, last


def fetch_bytes_with_retry(
    url: str,
    *,
    retries: int = 3,
    timeout: int = 90,
    opener: Callable[..., object] = urllib.request.urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> bytes:
    if retries < 1:
        raise ValueError("retries must be positive")
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = opener(url, timeout=timeout)
            data = response.read()
            if not data:
                raise OSError("empty response")
            return data
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                sleep(float(2**attempt))
    raise OSError(f"download failed after {retries} attempts: {url}") from last_error


def atomic_store_verified_zip(
    data: bytes,
    destination: Path,
    *,
    expected_sha256: str | None = None,
    replace: Callable[[str, str], None] = os.replace,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp", delete=False) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        verify_zip(temporary, expected_sha256=expected_sha256)
        replace(str(temporary), str(destination))
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def ensure_archive(
    *,
    url: str,
    destination: Path,
    checksum_text: str | None,
    retries: int = 3,
    opener: Callable[..., object] = urllib.request.urlopen,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[str, int, str, str, str]:
    expected = parse_checksum(checksum_text) if checksum_text is not None else None
    checksum_status = "official_checksum_verified" if expected else "official_checksum_unavailable_zip_crc_sha256_verified"
    if destination.exists():
        try:
            digest, count, first, last = verify_zip(destination, expected_sha256=expected)
            return digest, count, first, last, checksum_status
        except ValueError:
            destination.unlink()
    data = fetch_bytes_with_retry(url, retries=retries, opener=opener, sleep=sleep)
    atomic_store_verified_zip(data, destination, expected_sha256=expected)
    digest, count, first, last = verify_zip(destination, expected_sha256=expected)
    return digest, count, first, last, checksum_status
