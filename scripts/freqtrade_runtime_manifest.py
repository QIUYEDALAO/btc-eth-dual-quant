#!/usr/bin/env python3
"""Validate the sanitized, immutable Freqtrade runtime contract."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "freqtrade_lab" / "runtime-manifest.json"
DEFAULT_COMPOSE = ROOT / "freqtrade_lab" / "docker-compose.yml"
REQUIRED_COMMANDS = {
    "download-data",
    "list-data",
    "backtesting",
    "lookahead-analysis",
    "recursive-analysis",
    "webserver",
}
IMAGE_RE = re.compile(r"freqtradeorg/freqtrade:(?P<tag>[^@\s]+)@(?P<digest>sha256:[0-9a-f]{64})")


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"manifest must be a JSON object: {path}")
    return value


def _compose_image(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("image:"):
            return stripped.split(":", 1)[1].strip().strip('"').strip("'")
    raise ValueError(f"Compose image not found: {path}")


def validate_manifest(
    manifest_path: str | Path = DEFAULT_MANIFEST,
    compose_path: str | Path = DEFAULT_COMPOSE,
    observed_version: str | None = None,
) -> list[str]:
    manifest = _load_json(Path(manifest_path))
    compose_image = _compose_image(Path(compose_path))
    failures: list[str] = []
    image_ref = str(manifest.get("image_ref", ""))
    match = IMAGE_RE.fullmatch(image_ref)
    if match is None:
        failures.append("manifest image_ref must pin freqtradeorg/freqtrade tag and sha256 digest")
    if compose_image != image_ref:
        failures.append(f"Compose image mismatch: {compose_image} != {image_ref}")
    if match is not None:
        if str(manifest.get("release")) != match.group("tag"):
            failures.append("manifest release does not match image tag")
        if str(manifest.get("digest")) != match.group("digest"):
            failures.append("manifest digest does not match image digest")

    expected_version = str(manifest.get("freqtrade_version", ""))
    if expected_version != "freqtrade 2026.6":
        failures.append(f"unexpected Freqtrade version contract: {expected_version}")
    recorded_version = str(manifest.get("observed_version", ""))
    if expected_version not in recorded_version:
        failures.append("manifest observed_version does not contain the expected runtime version")
    if observed_version is not None and expected_version not in observed_version:
        failures.append(f"runtime version mismatch: expected {expected_version}")

    commands = manifest.get("command_categories", [])
    if not isinstance(commands, list) or set(map(str, commands)) != REQUIRED_COMMANDS:
        failures.append("manifest command_categories do not match the approved research entrypoints")
    data_range = manifest.get("public_data_range")
    if not isinstance(data_range, dict) or not data_range.get("start_utc") or not data_range.get("end_utc"):
        failures.append("manifest public_data_range is incomplete")
    generated = str(manifest.get("generated_utc", ""))
    try:
        datetime.fromisoformat(generated.replace("Z", "+00:00"))
    except ValueError:
        failures.append("manifest generated_utc is invalid")
    if manifest.get("api_key_used") is not False:
        failures.append("manifest must attest api_key_used=false")
    if manifest.get("runtime_artifacts_committed") is not False:
        failures.append("manifest must attest runtime_artifacts_committed=false")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate pinned Freqtrade runtime metadata")
    parser.add_argument("command", choices=("validate",), nargs="?", default="validate")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--compose", default=str(DEFAULT_COMPOSE))
    parser.add_argument("--observed-version", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = validate_manifest(args.manifest, args.compose, args.observed_version)
    if failures:
        print("Freqtrade runtime manifest FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Freqtrade runtime manifest PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
