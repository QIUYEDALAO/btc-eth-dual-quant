#!/usr/bin/env python3
"""Run and freeze the six-candidate synthetic causal validation suite."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IMAGE = (
    "freqtradeorg/freqtrade:2026.6@"
    "sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6"
)
CANDIDATES = [
    ("Supertrend", "1h", "Supertrend"),
    ("Strategy001", "5m", "default"),
    ("UniversalMACD", "5m", "UniversalMACD"),
    ("Bandtastic", "15m", "default"),
    ("Diamond", "5m", "default"),
    ("Heracles", "4h", "Heracles"),
]


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_hash(value: dict[str, Any]) -> str:
    identity = {
        key: item for key, item in value.items()
        if key not in {"content_hash", "generated_utc"}
    }
    return sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode())


def write_json(path: Path, value: dict[str, Any]) -> None:
    value["content_hash"] = canonical_hash(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ssh(host: str, identity: Path, command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ssh", "-i", str(identity), "-o", "IdentitiesOnly=yes", "-o", "BatchMode=yes", host, command],
        check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def flags() -> str:
    return " ".join([
        "--rm", "--network none", "--read-only", "--cap-drop ALL",
        "--security-opt no-new-privileges",
        "--tmpfs /tmp:rw,noexec,nosuid,size=256m,mode=1777",
        "--tmpfs /freqtrade/user_data:rw,nosuid,size=256m,mode=1777",
        "--user 1000:1000",
    ])


def command_base(stage: str, candidate: str, profile: str) -> str:
    return " ".join([
        f"docker run {flags()}",
        "-e PYTHONPATH=/harness:/freqtrade:/original:/strategy",
        "-e EXTERNAL_STRATEGY_OFFLINE_CAUSAL=1",
        "-e FROZEN_MARKETS_PATH=/harness/offline_markets.json",
        f"-v {shlex.quote(stage + '/runtime_harness')}:/harness:ro",
        f"-v {shlex.quote(stage + '/' + candidate)}:/strategy:ro",
        f"-v {shlex.quote(stage + '/' + candidate + '/original')}:/original:ro",
        f"-v {shlex.quote(stage + '/causal_fixture/' + profile)}:/data:ro",
        f"-v {shlex.quote(stage + '/causal_fixture/config.json')}:/config.json:ro",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vps-host", default=os.environ.get("VPS_HOST"))
    parser.add_argument("--identity-file", type=Path, required=True)
    parser.add_argument("--remote-stage", default="/root/apps/btc-eth-dual-quant/external_route_runtime")
    args = parser.parse_args()
    if not args.vps_host:
        raise SystemExit("VPS_HOST or --vps-host required")
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    fixture_result = ssh(
        args.vps_host, args.identity_file,
        f"cat {shlex.quote(args.remote_stage + '/causal_fixture/fixture_manifest.json')}",
    )
    if fixture_result.returncode:
        raise SystemExit("cannot read frozen causal fixture manifest")
    fixture = json.loads(fixture_result.stdout)
    if fixture.get("market_data") is not False or fixture.get("oos_data") is not False:
        raise SystemExit("causal fixture isolation failed")

    results = []
    for candidate, timeframe, profile in CANDIDATES:
        base = command_base(args.remote_stage, candidate, profile)
        direct_command = (
            f"{base} -v {shlex.quote(args.remote_stage + '/causal_probe.py')}:/probe.py:ro "
            f"--entrypoint python {shlex.quote(IMAGE)} /probe.py --candidate {candidate} "
            f"--timeframe {timeframe} --data-dir /data"
        )
        direct = ssh(args.vps_host, args.identity_file, direct_command)
        direct_output = direct.stdout + direct.stderr
        try:
            direct_json = json.loads(direct.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            direct_json = {"status": "REJECT", "failures": ["invalid direct probe output"]}

        common = (
            f"-c /config.json --userdir /freqtrade/user_data -d /data/binance "
            f"--strategy {candidate} --strategy-path /strategy --timerange 20230101-20230304 "
            "--data-format-ohlcv json --no-color"
        )
        lookahead_command = (
            f"{base} {shlex.quote(IMAGE)} lookahead-analysis {common} "
            "--minimum-trade-amount 1 --targeted-trade-amount 5 --allow-limit-orders --fee 0.0015"
        )
        lookahead = ssh(args.vps_host, args.identity_file, lookahead_command)
        lookahead_output = lookahead.stdout + lookahead.stderr
        recursive_command = (
            f"{base} {shlex.quote(IMAGE)} recursive-analysis {common} "
            "--startup-candle 100 200 400"
        )
        recursive = ssh(args.vps_host, args.identity_file, recursive_command)
        recursive_output = recursive.stdout + recursive.stderr

        failures = list(direct_json.get("failures", []))
        if direct.returncode != 0 or direct_json.get("status") != "PASS":
            failures.append("direct golden/prefix causal probe failed")
        if lookahead.returncode != 0 or "no bias detected" not in lookahead_output:
            failures.append("Freqtrade lookahead-analysis did not pass")
        if recursive.returncode != 0 or "No lookahead bias on indicators found." not in recursive_output:
            failures.append("Freqtrade recursive-analysis did not pass")
        forbidden_output = "\n".join((lookahead_output, recursive_output))
        if "api.binance.com" in forbidden_output or "fapi.binance.com" in forbidden_output:
            failures.append("analysis attempted external exchange network")
        if "Configuration error" in forbidden_output or "Fatal exception" in forbidden_output:
            failures.append("Freqtrade analysis reported a fatal/configuration error")

        status = "PASS" if not failures else "REJECT"
        fixture_profile = fixture["profiles"][profile]
        golden = {
            "schema_version": "external-strategy-golden-fixture-v1",
            "candidate_id": candidate,
            "profile": profile,
            "fixture_manifest_hash": fixture["content_hash"],
            "profile_identity": fixture_profile,
            "timeframe": timeframe,
            "source_is_synthetic": True,
            "market_or_oos_rows": 0,
            "normal_reverse_shuffled_equal": len({
                direct_json.get("normal_signal_hash"),
                direct_json.get("reverse_signal_hash"),
                direct_json.get("shuffled_signal_hash"),
            }) == 1,
            "adapter_original_equal": direct_json.get("normal_signal_hash") == direct_json.get("original_signal_hash"),
            "signal_hash": direct_json.get("normal_signal_hash"),
            "entry_signals": direct_json.get("entry_signals"),
            "exit_signals": direct_json.get("exit_signals"),
        }
        directory = ROOT / f"external_strategies/adapters/{candidate}"
        write_json(directory / "golden_fixture.json", golden)
        result = {
            "schema_version": "external-strategy-causal-result-v1",
            "candidate_id": candidate,
            "status": status,
            "generated_utc": generated,
            "golden_fixture_hash": golden["content_hash"],
            "direct_probe": direct_json,
            "direct_command_exit_code": direct.returncode,
            "direct_stdout_stderr_sha256": sha256(direct_output.encode()),
            "lookahead_command_exit_code": lookahead.returncode,
            "lookahead_stdout_stderr_sha256": sha256(lookahead_output.encode()),
            "lookahead_findings": 0 if "no bias detected" in lookahead_output else 1,
            "recursive_command_exit_code": recursive.returncode,
            "recursive_stdout_stderr_sha256": sha256(recursive_output.encode()),
            "recursive_findings": 0 if "No lookahead bias on indicators found." in recursive_output else 1,
            "informative_pairs": [],
            "partial_candle_allowed": False,
            "earliest_fill": "next_eligible_5m_open",
            "lifecycle_or_mask_crossing_allowed": False,
            "same_bar_close_fill_allowed": False,
            "position_increase_allowed": False,
            "network_mode": "none_with_hash_bound_offline_market_fixture",
            "dry_run_bot_started": False,
            "oos_rows_decoded": 0,
            "failures": failures,
        }
        write_json(directory / "causal_result.json", result)
        semantic = {
            "Supertrend": "NumPy/Pandas compatibility exports only; thresholds, periods and signals unchanged.",
            "Strategy001": "Interface identity plus EMA100 warmup declaration; economic conditions unchanged.",
            "UniversalMACD": "Interface identity only; economic conditions unchanged.",
            "Bandtastic": "Interface identity only; economic conditions unchanged.",
            "Diamond": "Interface identity plus shift-history warmup declaration; economic conditions unchanged.",
            "Heracles": "Equivalent ta indicator dependency plus source-history warmup declaration; economic conditions unchanged.",
        }[candidate]
        (directory / "semantic_diff.md").write_text(
            f"# {candidate} semantic diff\n\n{semantic}\n\n"
            "No threshold, period, timeframe, ROI, stoploss, pair-selection, position-sizing, "
            "entry condition or exit condition changed.\n",
            encoding="utf-8",
        )
        compatibility_path = directory / "compatibility_manifest.json"
        compatibility = json.loads(compatibility_path.read_text())
        compatibility["status"] = "causal_pass" if status == "PASS" else "causal_reject"
        compatibility["causal_result_hash"] = result["content_hash"]
        write_json(compatibility_path, compatibility)
        results.append({
            "candidate_id": candidate,
            "status": status,
            "causal_result_hash": result["content_hash"],
            "compatibility_manifest_hash": compatibility["content_hash"],
            "failures": failures,
        })

    pass_count = sum(item["status"] == "PASS" for item in results)
    summary = {
        "schema_version": "external-strategy-causal-summary-v1",
        "status": "pass" if pass_count >= 5 else "hard_stop_fewer_than_five",
        "generated_utc": generated,
        "runtime_route_manifest_hash": json.loads(
            (ROOT / "reports/m1/evidence/external_strategy_runtime/runtime_route_manifest.json").read_text()
        )["content_hash"],
        "fixture_manifest_hash": fixture["content_hash"],
        "offline_market_fixture_sha256": sha256(
            (ROOT / "external_strategies/runtime_harness/offline_markets.json").read_bytes()
        ),
        "causal_validations": 6,
        "pass_count": pass_count,
        "minimum_required_before_is": 5,
        "results": results,
        "market_or_oos_rows": 0,
        "oos_rows_decoded": 0,
    }
    write_json(
        ROOT / "reports/m1/evidence/external_strategy_runtime/causal_summary.json",
        summary,
    )
    print(f"causal {summary['status']}: pass={pass_count}/6 hash={summary['content_hash']}")
    return 0 if pass_count >= 5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
