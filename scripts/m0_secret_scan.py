#!/usr/bin/env python3
"""M0 high-confidence secret scanner.

Scans git-indexed files for real secret values while allowing environment
variable names such as BINANCE_API_KEY and BINANCE_API_SECRET in code.
"""

from __future__ import annotations

import math
import re
import subprocess
import sys
from pathlib import Path


EXCLUDED_PREFIXES = (
    ".deps/",
    ".venv/",
    "venv/",
    "storage/raw/",
    "storage/duckdb/",
    "storage/logs/",
)

ALLOWED_ENV_FILES = {".env.example"}
PLACEHOLDERS = {
    "",
    "<placeholder>",
    "<your_api_key>",
    "<your_api_secret>",
    "your_api_key_here",
    "your_api_secret_here",
    "YOUR_API_KEY_HERE",
    "YOUR_API_SECRET_HERE",
}

ASSIGNMENT_RE = re.compile(
    r"""(?P<name>BINANCE_API_KEY|BINANCE_API_SECRET|api_secret|api_key|apiKey|secretKey)\s*[:=]\s*(?P<quote>['"])(?P<value>[^'"]*)(?P=quote)"""
)
SK_TOKEN_RE = re.compile(r"""sk-[A-Za-z0-9_-]{16,}""")
PRIVATE_KEY_RE = re.compile(r"""BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY""")
LONG_TOKEN_RE = re.compile(r"""(?<![A-Za-z0-9])([A-Za-z0-9_+/=-]{32,})(?![A-Za-z0-9])""")


def git_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def is_excluded(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {char: value.count(char) for char in set(value)}
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def is_placeholder(value: str) -> bool:
    stripped = value.strip()
    return stripped in PLACEHOLDERS or stripped.upper() in PLACEHOLDERS


def looks_like_hash(value: str) -> bool:
    return len(value) in {32, 40, 64, 128} and re.fullmatch(r"[0-9a-f]+", value) is not None


def looks_like_high_entropy_secret(value: str) -> bool:
    if len(value) < 32 or is_placeholder(value) or looks_like_hash(value):
        return False
    if "/" in value or "\\" in value or "." in value:
        return False
    if "_" in value and value.upper() == value:
        return False
    has_lower = any(char.islower() for char in value)
    has_upper = any(char.isupper() for char in value)
    has_digit = any(char.isdigit() for char in value)
    has_symbol = any(char in "_+/=-" for char in value)
    variety = sum([has_lower, has_upper, has_digit, has_symbol])
    return has_lower and has_upper and has_digit and variety >= 3 and shannon_entropy(value) >= 4.2


def scan_file(path: str) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if SK_TOKEN_RE.search(line):
            findings.append((line_no, "openai_style_sk_token"))
        if PRIVATE_KEY_RE.search(line):
            findings.append((line_no, "private_key_block"))
        for match in ASSIGNMENT_RE.finditer(line):
            value = match.group("value")
            if len(value) >= 16 and not is_placeholder(value):
                findings.append((line_no, f"hardcoded_secret_assignment:{match.group('name')}"))
        for match in LONG_TOKEN_RE.finditer(line):
            value = match.group(1)
            if looks_like_high_entropy_secret(value):
                findings.append((line_no, "high_entropy_32_plus_token"))
    return findings


def main() -> int:
    findings: list[tuple[str, int, str]] = []
    for path in git_files():
        if is_excluded(path):
            continue
        name = Path(path).name
        if (name == ".env" or (name.startswith(".env.") and name not in ALLOWED_ENV_FILES)) and path not in ALLOWED_ENV_FILES:
            findings.append((path, 1, "tracked_env_file"))
            continue
        for line_no, reason in scan_file(path):
            findings.append((path, line_no, reason))

    for path, line_no, reason in findings:
        print(f"{path}:{line_no}: {reason}")
    if findings:
        print(f"M0 secret scan FAIL: {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print("M0 secret scan PASS: no real secret values found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
