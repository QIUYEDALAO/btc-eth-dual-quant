#!/usr/bin/env python3
"""Collect the approved, result-free external-strategy runtime evidence."""

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
    ("Supertrend", "external_strategies/original/01-Supertrend/Supertrend.py"),
    ("Strategy001", "external_strategies/original/03-Strategy001/Strategy001.py"),
    ("UniversalMACD", "external_strategies/original/05-UniversalMACD/UniversalMACD.py"),
    ("Bandtastic", "external_strategies/original/07-Bandtastic/Bandtastic.py"),
    ("Diamond", "external_strategies/original/09-Diamond/Diamond.py"),
    ("Heracles", "external_strategies/original/11-Heracles/Heracles.py"),
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_hash(value: dict[str, Any]) -> str:
    identity = {
        key: item for key, item in value.items()
        if key not in {"content_hash", "generated_utc"}
    }
    raw = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(raw.encode())


def write_manifest(path: Path, value: dict[str, Any]) -> None:
    value["content_hash"] = canonical_hash(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ssh_command(host: str, identity_file: Path, remote: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "ssh", "-i", str(identity_file), "-o", "IdentitiesOnly=yes",
            "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, remote,
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def container_flags() -> str:
    return " ".join([
        "--rm", "--network none", "--read-only", "--cap-drop ALL",
        "--security-opt no-new-privileges",
        "--tmpfs /tmp:rw,noexec,nosuid,size=64m,mode=1777",
        "--tmpfs /freqtrade/user_data:rw,nosuid,size=64m,mode=1777",
        "--user 1000:1000",
    ])


def require_success(result: subprocess.CompletedProcess[str], label: str) -> str:
    if result.returncode != 0:
        raise SystemExit(f"{label} failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vps-host", default=os.environ.get("VPS_HOST"))
    parser.add_argument("--identity-file", type=Path, required=True)
    parser.add_argument(
        "--remote-stage",
        default="/root/apps/btc-eth-dual-quant/external_route_runtime",
    )
    args = parser.parse_args()
    if not args.vps_host:
        raise SystemExit("VPS_HOST or --vps-host is required")
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    host_probe = require_success(
        ssh_command(
            args.vps_host,
            args.identity_file,
            "set -eu; hostname; uname -s; uname -r; uname -m; "
            "docker version --format '{{json .}}'; "
            f"docker image inspect {shlex.quote(IMAGE)} --format '{{{{json .}}}}'",
        ),
        "host identity",
    ).splitlines()
    if len(host_probe) != 6:
        raise SystemExit("unexpected host identity output")
    docker_version = json.loads(host_probe[4])
    image_inspect = json.loads(host_probe[5])
    image_id = image_inspect.get("Id")
    if image_id != IMAGE.split("@", 1)[1]:
        raise SystemExit("pinned image identity drift")

    dependency_code = (
        "import json,platform,sys; import ccxt,numpy,pandas,talib,technical; "
        "print(json.dumps({'python':sys.version.split()[0],"
        "'platform':platform.platform(),'ccxt':ccxt.__version__,"
        "'numpy':numpy.__version__,'pandas':pandas.__version__,"
        "'talib':talib.__version__,'technical':getattr(technical,'__version__','unknown')},"
        "sort_keys=True,separators=(',',':')))"
    )
    dependency_output = require_success(
        ssh_command(
            args.vps_host,
            args.identity_file,
            f"docker run {container_flags()} --entrypoint python {shlex.quote(IMAGE)} "
            f"-c {shlex.quote(dependency_code)}",
        ),
        "dependency identity",
    ).strip()
    dependencies = json.loads(dependency_output)

    evidence_dir = ROOT / "reports/m1/evidence/external_strategy_runtime"
    runtime_identity = {
        "schema_version": "external-strategy-runtime-identity-v1",
        "status": "pass",
        "generated_utc": generated,
        "server_label": "configured_vps",
        "hostname_sha256": sha256_bytes(host_probe[0].encode()),
        "os": host_probe[1],
        "kernel": host_probe[2],
        "architecture": host_probe[3],
        "docker_client_version": docker_version["Client"]["Version"],
        "docker_server_version": docker_version["Server"]["Version"],
        "image": IMAGE,
        "image_id": image_id,
        "configured_image_user": image_inspect.get("Config", {}).get("User"),
        "runtime_user": "1000:1000",
        "freqtrade_version": "freqtrade 2026.6",
        "network": "none",
        "root_filesystem": "read_only",
        "strategy_source": "read_only_mount",
        "capabilities": "all_dropped",
        "no_new_privileges": True,
        "secrets_mounted": False,
        "api_or_private_endpoint_used": False,
        "dry_run_or_trading_used": False,
        "oos_rows_decoded": 0,
    }
    container_manifest = {
        "schema_version": "external-strategy-container-manifest-v1",
        "status": "pass",
        "generated_utc": generated,
        "image": IMAGE,
        "image_id": image_id,
        "repo_digests": sorted(image_inspect.get("RepoDigests", [])),
        "platform": {"os": image_inspect.get("Os"), "architecture": image_inspect.get("Architecture")},
        "configured_user": image_inspect.get("Config", {}).get("User"),
        "security_flags": container_flags().split(),
    }
    dependency_manifest = {
        "schema_version": "external-strategy-dependency-manifest-v1",
        "status": "pass",
        "generated_utc": generated,
        "image": IMAGE,
        "dependencies": dependencies,
        "dependency_probe_stdout_sha256": sha256_bytes(dependency_output.encode()),
    }
    write_manifest(evidence_dir / "runtime_identity.json", runtime_identity)
    write_manifest(evidence_dir / "container_manifest.json", container_manifest)
    write_manifest(evidence_dir / "dependency_manifest.json", dependency_manifest)

    freeze = json.loads((ROOT / "config/external_strategy_candidate_freeze_v1.json").read_text())
    frozen = {item["id"]: item for item in freeze["frozen_candidates"]}
    probe_hash = sha256_bytes((ROOT / "scripts/external_strategy_runtime_probe.py").read_bytes())
    candidate_results = []
    for candidate, original_relative in CANDIDATES:
        remote_candidate = f"{args.remote_stage}/{candidate}"
        mounts = (
            f"-e PYTHONPATH=/freqtrade:/original:/strategy "
            f"-v {shlex.quote(remote_candidate)}:/strategy:ro "
            f"-v {shlex.quote(remote_candidate + '/original')}:/original:ro "
            f"-v {shlex.quote(args.remote_stage + '/runtime_probe.py')}:/probe.py:ro"
        )
        load_result = ssh_command(
            args.vps_host,
            args.identity_file,
            f"docker run {container_flags()} {mounts} {shlex.quote(IMAGE)} "
            f"list-strategies --strategy-path /strategy --no-color",
        )
        load_output = load_result.stdout + load_result.stderr
        if load_result.returncode != 0 or candidate not in load_output or "LOAD FAILED" in load_output:
            raise SystemExit(f"strategy load failed: {candidate}")
        probe_result = ssh_command(
            args.vps_host,
            args.identity_file,
            f"docker run {container_flags()} {mounts} --entrypoint python {shlex.quote(IMAGE)} "
            f"/probe.py --candidate {shlex.quote(candidate)}",
        )
        probe_output = require_success(probe_result, f"runtime probe {candidate}").strip()
        probe = json.loads(probe_output.splitlines()[-1])
        local_adapter = ROOT / f"external_strategies/adapters/{candidate}/adapter.py"
        original = ROOT / original_relative
        if probe["base_adapter_hash"] != sha256_bytes(local_adapter.read_bytes()):
            raise SystemExit(f"adapter hash mismatch: {candidate}")
        if probe["executable_components"]["original_sha256"] != sha256_bytes(original.read_bytes()):
            raise SystemExit(f"original hash mismatch: {candidate}")
        if probe["observed_external_parameter_file_count"] != 0 or probe["observed_config_override_count"] != 0:
            raise SystemExit(f"runtime parameter override detected: {candidate}")
        identity = {
            "schema_version": "external-strategy-original-identity-v1",
            "candidate_id": candidate,
            "source_path": original_relative,
            "source_sha256": frozen[candidate]["source_sha256"],
            "source_commit": frozen[candidate]["commit"],
            "source_declaration_hash": frozen[candidate]["source_declaration_hash"],
        }
        compatibility = {
            "schema_version": "external-strategy-compatibility-manifest-v1",
            "candidate_id": candidate,
            "status": "runtime_load_pass_causal_pending",
            "generated_utc": generated,
            "runtime_identity_hash": runtime_identity["content_hash"],
            "container_manifest_hash": container_manifest["content_hash"],
            "dependency_manifest_hash": dependency_manifest["content_hash"],
            "runtime_probe_sha256": probe_hash,
            "load_command_kind": "freqtrade_list_strategies",
            "load_exit_code": load_result.returncode,
            "load_stdout_stderr_sha256": sha256_bytes(load_output.encode()),
            **probe,
        }
        directory = ROOT / f"external_strategies/adapters/{candidate}"
        write_manifest(directory / "original_identity.json", identity)
        write_manifest(directory / "compatibility_manifest.json", compatibility)
        candidate_results.append({
            "candidate_id": candidate,
            "load_status": "PASS",
            "compatibility_manifest_hash": compatibility["content_hash"],
            "base_adapter_hash": probe["base_adapter_hash"],
            "variant_executable_hash": probe["variant_executable_hash"],
            "runtime_effective_settings_hash": probe["runtime_effective_settings_hash"],
            "runtime_resolved_parameters_hash": probe["runtime_resolved_parameters_hash"],
            "observed_external_parameter_file_count": 0,
            "observed_config_override_count": 0,
        })

    route = {
        "schema_version": "external-strategy-runtime-route-v1",
        "status": "runtime_identity_and_six_loads_pass_causal_pending",
        "generated_utc": generated,
        "adr0017_hash": "8a4b1d6d859c683bf3a61fd55784083bc04c8169a9cd1cab2362273177b48cdd",
        "runtime_identity_hash": runtime_identity["content_hash"],
        "container_manifest_hash": container_manifest["content_hash"],
        "dependency_manifest_hash": dependency_manifest["content_hash"],
        "candidates": candidate_results,
        "freqtrade_loads": 6,
        "causal_validations": 0,
        "is_trials": 0,
        "selection_trial_count": 0,
        "oos_authorized": False,
        "oos_opened": False,
        "oos_runs": 0,
        "oos_rows_decoded": 0,
        "dry_run": False,
        "api_live": False,
        "m2": False,
    }
    write_manifest(evidence_dir / "runtime_route_manifest.json", route)
    print(f"runtime PASS: {runtime_identity['content_hash']} loads=6 causal=0 is=0 oos_rows=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
