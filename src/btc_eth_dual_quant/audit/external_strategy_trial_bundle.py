"""Atomic, result-agnostic storage for external-strategy IS trial evidence.

This module deliberately does not run Freqtrade or interpret strategy results.
An injected executor returns the bodies of the twelve frozen result documents.
They are written below a private staging directory, flushed to durable storage,
and made authoritative by one same-filesystem directory rename.  The resulting
``<trial_id>/`` directory is the sole materialization fact.

Failures before that rename produce an append-only incident which contains no
performance values.  Recovery after the rename derives the governance marker
from the immutable bundle and has no executor argument, so recovery cannot
silently rerun performance work.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
from typing import Any, Callable, Mapping
import uuid


SCENARIOS = ("Base", "CostX2", "StressA", "StressB")
KINDS = ("trades", "equity", "metrics")
RESULT_SCHEMA_VERSION = "external-strategy-is-result-v1"
BUNDLE_SCHEMA_VERSION = "external-strategy-atomic-trial-bundle-v1"
INCIDENT_SCHEMA_VERSION = "external-strategy-pre-materialization-incident-v1"
GOVERNANCE_SCHEMA_VERSION = "external-strategy-trial-governance-marker-v1"

REQUIRED_BASE_ENVELOPE_FIELDS = frozenset(
    {
        "schema_version",
        "trial_id",
        "candidate_id",
        "variant_id",
        "variant_type",
        "source_hash",
        "source_declaration_hash",
        "candidate_freeze_hash",
        "unified_is_protocol_hash",
        "data_authority_hash",
        "benchmark_contract_hash",
        "dsr_reference_hash",
        "original_is_authority_hash",
        "runtime_route_manifest_hash",
        "causal_summary_hash",
        "boundary_authority_hash",
        "base_adapter_hash",
        "variant_executable_hash",
        "runtime_effective_settings_hash",
        "runtime_resolved_parameters_hash",
        "modification_package_id",
        "modification_package_hash",
        "first_materialized_utc",
        "append_only",
    }
)
RESULT_ENVELOPE_FIELDS = REQUIRED_BASE_ENVELOPE_FIELDS | {"scenario", "kind"}
_TRIAL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_TOKEN = re.compile(r"[A-Za-z0-9]{8,64}\Z")


class TrialBundleError(RuntimeError):
    """Base class for fail-closed bundle state errors."""


class TrialBundleExists(TrialBundleError):
    """The requested trial already has an authoritative bundle."""


class TrialTerminalIncident(TrialBundleError):
    """A pre-materialization incident permanently closed this trial id."""


class TrialExecutorError(TrialBundleError):
    """The injected executor failed before atomic materialization."""


class SimulatedTrialCrash(TrialBundleError):
    """Test-only crash injection at a durable state boundary."""


@dataclass(frozen=True)
class BundleReceipt:
    trial_id: str
    directory: Path
    bundle_content_hash: str
    manifest_byte_sha256: str
    result_file_count: int
    governance_complete: bool


Executor = Callable[[str], Mapping[str, Mapping[str, Any]]]


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def semantic_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def byte_hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_trial_id(trial_id: str) -> str:
    if not isinstance(trial_id, str) or _TRIAL_ID.fullmatch(trial_id) is None:
        raise TrialBundleError("invalid trial_id")
    return trial_id


def _validate_token(token: str) -> str:
    if _TOKEN.fullmatch(token) is None:
        raise TrialBundleError("invalid staging token")
    return token


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_directory(path: Path) -> None:
    if path.exists():
        if not path.is_dir() or path.is_symlink():
            raise TrialBundleError(f"unsafe state directory: {path.name}")
        return
    path.mkdir(parents=True, mode=0o700)
    _fsync_directory(path.parent)


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _write_bytes_exclusive(path: Path, value: bytes, *, mode: int = 0o444) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)
    os.chmod(path, mode)
    _fsync_directory(path.parent)


def _write_json_exclusive(path: Path, value: Mapping[str, Any], *, mode: int = 0o444) -> bytes:
    encoded = _json_bytes(value)
    _write_bytes_exclusive(path, encoded, mode=mode)
    return encoded


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TrialBundleError(f"invalid JSON evidence: {path.name}") from exc
    if not isinstance(value, dict):
        raise TrialBundleError(f"JSON evidence must be an object: {path.name}")
    return value


def _validate_base_envelope(trial_id: str, envelope: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(envelope, Mapping):
        raise TrialBundleError("base envelope must be a mapping")
    result = dict(envelope)
    missing = REQUIRED_BASE_ENVELOPE_FIELDS - set(result)
    if missing:
        raise TrialBundleError(f"base envelope fields missing: {sorted(missing)}")
    if result.get("schema_version") != RESULT_SCHEMA_VERSION or result.get("trial_id") != trial_id:
        raise TrialBundleError("base envelope schema or trial identity mismatch")
    if "scenario" in result or "kind" in result:
        raise TrialBundleError("base envelope cannot predeclare scenario or kind")
    return result


def _result_basename(trial_id: str, scenario: str, kind: str) -> str:
    return f"{trial_id}.{scenario}.{kind}.json"


def _relative_result_path(trial_id: str, basename: str) -> str:
    return str(PurePosixPath(trial_id, basename))


def _state_paths(root: Path) -> tuple[Path, Path, Path]:
    return root / ".staging", root / ".incidents", root / ".governance"


def _incident_path(root: Path, trial_id: str, token: str) -> Path:
    return root / ".incidents" / f"{trial_id}--{token}.json"


def incident_paths(root: Path, trial_id: str) -> tuple[Path, ...]:
    _validate_trial_id(trial_id)
    directory = root / ".incidents"
    if not directory.is_dir():
        return ()
    return tuple(sorted(directory.glob(f"{trial_id}--*.json")))


def _record_incident(
    root: Path,
    *,
    trial_id: str,
    token: str,
    reason: str,
    executor_invocations: int | None,
) -> Path:
    _, incidents, _ = _state_paths(root)
    _ensure_directory(incidents)
    payload: dict[str, Any] = {
        "schema_version": INCIDENT_SCHEMA_VERSION,
        "trial_id": trial_id,
        "incident_token": token,
        "reason": reason,
        "performance_materialized": False,
        "result_values_recorded": False,
        "bundle_exists": False,
        "executor_invocations": executor_invocations,
        "terminal_no_automatic_rerun": True,
    }
    payload["content_hash"] = semantic_hash(payload)
    path = _incident_path(root, trial_id, token)
    if path.exists():
        if _load_json_object(path) != payload:
            raise TrialBundleError("incident identity collision")
        return path
    _write_json_exclusive(path, payload)
    return path


def _remove_staging(path: Path) -> None:
    if not path.exists():
        return
    if path.is_symlink() or not path.is_dir():
        raise TrialBundleError("unsafe staging path")
    os.chmod(path, 0o700)
    for child in path.iterdir():
        if child.is_symlink() or not child.is_file():
            raise TrialBundleError("unsafe staging content")
        os.chmod(child, 0o600)
    shutil.rmtree(path)
    _fsync_directory(path.parent)


def recover_orphaned_staging(root: Path, *, trial_id: str | None = None) -> tuple[Path, ...]:
    """Convert abandoned, non-authoritative staging directories to incidents."""

    root = Path(root)
    if trial_id is not None:
        _validate_trial_id(trial_id)
    staging, incidents, _ = _state_paths(root)
    if not staging.is_dir():
        return ()
    _ensure_directory(incidents)
    recovered: list[Path] = []
    for path in sorted(staging.iterdir()):
        if path.is_symlink() or not path.is_dir() or "--" not in path.name:
            raise TrialBundleError("unsafe orphaned staging entry")
        staged_trial, token = path.name.rsplit("--", 1)
        _validate_trial_id(staged_trial)
        _validate_token(token)
        if trial_id is not None and staged_trial != trial_id:
            continue
        if (root / staged_trial).exists():
            raise TrialBundleError("staging and materialized bundle coexist")
        recovered.append(
            _record_incident(
                root,
                trial_id=staged_trial,
                token=token,
                reason="orphaned_staging_recovered",
                executor_invocations=None,
            )
        )
        _remove_staging(path)
    return tuple(recovered)


def _validate_descriptor_path(trial_id: str, path_text: object, expected_basename: str) -> str:
    if not isinstance(path_text, str):
        raise TrialBundleError("result descriptor path must be text")
    pure = PurePosixPath(path_text)
    if pure.is_absolute() or pure.parts != (trial_id, expected_basename):
        raise TrialBundleError("result path must be exactly <trial_id>/<basename>")
    return path_text


def validate_trial_bundle(root: Path, trial_id: str) -> BundleReceipt:
    root = Path(root)
    _validate_trial_id(trial_id)
    directory = root / trial_id
    if not directory.is_dir() or directory.is_symlink():
        raise TrialBundleError("materialized trial bundle missing or unsafe")
    manifest_path = directory / "trial.bundle.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise TrialBundleError("trial bundle manifest missing or unsafe")
    manifest_bytes = manifest_path.read_bytes()
    manifest = _load_json_object(manifest_path)
    expected_manifest_fields = {
        "schema_version",
        "trial_id",
        "base_envelope",
        "result_file_count",
        "result_files",
        "bundle_content_hash",
    }
    if set(manifest) != expected_manifest_fields:
        raise TrialBundleError("trial bundle manifest fields changed")
    if manifest.get("schema_version") != BUNDLE_SCHEMA_VERSION or manifest.get("trial_id") != trial_id:
        raise TrialBundleError("trial bundle schema or identity mismatch")
    envelope = _validate_base_envelope(trial_id, manifest.get("base_envelope", {}))
    descriptors = manifest.get("result_files")
    if not isinstance(descriptors, list) or len(descriptors) != len(SCENARIOS) * len(KINDS):
        raise TrialBundleError("trial bundle must contain exactly twelve result descriptors")
    content = {key: value for key, value in manifest.items() if key != "bundle_content_hash"}
    if manifest.get("bundle_content_hash") != semantic_hash(content):
        raise TrialBundleError("trial bundle content hash mismatch")

    expected_pairs = {(scenario, kind) for scenario in SCENARIOS for kind in KINDS}
    actual_pairs: set[tuple[str, str]] = set()
    referenced_paths: set[str] = set()
    expected_files = {"trial.bundle.json"}
    for descriptor in descriptors:
        if not isinstance(descriptor, dict) or set(descriptor) != {
            "path",
            "scenario",
            "kind",
            "byte_sha256",
            "semantic_hash",
        }:
            raise TrialBundleError("result descriptor fields changed")
        scenario, kind = descriptor.get("scenario"), descriptor.get("kind")
        if (scenario, kind) not in expected_pairs or (scenario, kind) in actual_pairs:
            raise TrialBundleError("result scenario/kind coverage is invalid")
        actual_pairs.add((scenario, kind))
        basename = _result_basename(trial_id, str(scenario), str(kind))
        relative = _validate_descriptor_path(trial_id, descriptor.get("path"), basename)
        if relative in referenced_paths:
            raise TrialBundleError("result path reused")
        referenced_paths.add(relative)
        expected_files.add(basename)
        result_path = root / PurePosixPath(relative)
        if result_path.parent != directory or result_path.is_symlink() or not result_path.is_file():
            raise TrialBundleError("result path escapes bundle or is missing")
        raw = result_path.read_bytes()
        if byte_hash(raw) != descriptor.get("byte_sha256"):
            raise TrialBundleError("result byte hash mismatch")
        payload = _load_json_object(result_path)
        if semantic_hash(payload) != descriptor.get("semantic_hash"):
            raise TrialBundleError("result semantic hash mismatch")
        expected_envelope = {**envelope, "scenario": scenario, "kind": kind}
        if any(payload.get(field) != value for field, value in expected_envelope.items()):
            raise TrialBundleError("result envelope mismatch")
        if not RESULT_ENVELOPE_FIELDS <= set(payload):
            raise TrialBundleError("result envelope incomplete")
    if actual_pairs != expected_pairs:
        raise TrialBundleError("result scenario/kind coverage is incomplete")
    actual_files = {path.name for path in directory.iterdir()}
    if actual_files != expected_files or any(path.is_symlink() for path in directory.iterdir()):
        raise TrialBundleError("trial bundle contains unexpected files")
    return BundleReceipt(
        trial_id=trial_id,
        directory=directory,
        bundle_content_hash=str(manifest["bundle_content_hash"]),
        manifest_byte_sha256=byte_hash(manifest_bytes),
        result_file_count=len(descriptors),
        governance_complete=(root / ".governance" / f"{trial_id}.json").is_file(),
    )


def _governance_payload(receipt: BundleReceipt) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": GOVERNANCE_SCHEMA_VERSION,
        "trial_id": receipt.trial_id,
        "bundle_content_hash": receipt.bundle_content_hash,
        "manifest_byte_sha256": receipt.manifest_byte_sha256,
        "result_file_count": receipt.result_file_count,
        "performance_materialized": True,
        "selection_trial_increment": 1,
        "executor_reinvoked_during_recovery": False,
    }
    payload["content_hash"] = semantic_hash(payload)
    return payload


def recover_trial_bundle(root: Path, trial_id: str) -> BundleReceipt:
    """Validate a materialized bundle and idempotently complete governance.

    There is intentionally no executor parameter.  Recovery can only inspect
    the already materialized bundle and write its derived governance marker.
    """

    root = Path(root)
    receipt = validate_trial_bundle(root, trial_id)
    _, _, governance = _state_paths(root)
    _ensure_directory(governance)
    payload = _governance_payload(receipt)
    marker = governance / f"{trial_id}.json"
    if marker.exists():
        if marker.is_symlink() or _load_json_object(marker) != payload:
            raise TrialBundleError("governance marker drift")
    else:
        _write_json_exclusive(marker, payload)
    return replace(receipt, governance_complete=True)


def materialized_trial_ids(root: Path) -> tuple[str, ...]:
    root = Path(root)
    if not root.is_dir():
        return ()
    result: list[str] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.name.startswith(".") or not path.is_dir():
            continue
        _validate_trial_id(path.name)
        validate_trial_bundle(root, path.name)
        result.append(path.name)
    return tuple(result)


def materialize_trial_bundle(
    root: Path,
    *,
    trial_id: str,
    base_envelope: Mapping[str, Any],
    executor: Executor,
    crash_at: str | None = None,
    staging_token: str | None = None,
) -> BundleReceipt:
    """Build and atomically publish one complete four-scenario result bundle."""

    root = Path(root)
    _validate_trial_id(trial_id)
    envelope = _validate_base_envelope(trial_id, base_envelope)
    if crash_at not in {None, "pre_rename", "post_rename"}:
        raise TrialBundleError("unknown crash injection point")
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise TrialBundleError("trial root cannot be a symlink")
    staging, incidents, governance = _state_paths(root)
    for path in (staging, incidents, governance):
        _ensure_directory(path)
    recover_orphaned_staging(root, trial_id=trial_id)
    final = root / trial_id
    if final.exists():
        raise TrialBundleExists(f"trial already materialized: {trial_id}")
    if incident_paths(root, trial_id):
        raise TrialTerminalIncident(f"trial has a terminal pre-materialization incident: {trial_id}")

    token = _validate_token(staging_token or uuid.uuid4().hex)
    stage = staging / f"{trial_id}--{token}"
    try:
        stage.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise TrialBundleError("staging identity collision") from exc
    _fsync_directory(staging)
    invocations = 0
    descriptors: list[dict[str, Any]] = []
    try:
        for scenario in SCENARIOS:
            try:
                outputs = executor(scenario)
                invocations += 1
            except Exception as exc:
                raise TrialExecutorError("executor failed before atomic materialization") from exc
            if not isinstance(outputs, Mapping) or set(outputs) != set(KINDS):
                raise TrialBundleError("executor must return exactly trades/equity/metrics")
            for kind in KINDS:
                body = outputs[kind]
                if not isinstance(body, Mapping):
                    raise TrialBundleError("executor result body must be a mapping")
                if RESULT_ENVELOPE_FIELDS & set(body):
                    raise TrialBundleError("executor body cannot override result envelope")
                payload = {**envelope, "scenario": scenario, "kind": kind, **dict(body)}
                basename = _result_basename(trial_id, scenario, kind)
                encoded = _write_json_exclusive(stage / basename, payload)
                descriptors.append(
                    {
                        "path": _relative_result_path(trial_id, basename),
                        "scenario": scenario,
                        "kind": kind,
                        "byte_sha256": byte_hash(encoded),
                        "semantic_hash": semantic_hash(payload),
                    }
                )
        manifest: dict[str, Any] = {
            "schema_version": BUNDLE_SCHEMA_VERSION,
            "trial_id": trial_id,
            "base_envelope": envelope,
            "result_file_count": len(descriptors),
            "result_files": descriptors,
        }
        manifest["bundle_content_hash"] = semantic_hash(manifest)
        _write_json_exclusive(stage / "trial.bundle.json", manifest)
        _fsync_directory(stage)
        if crash_at == "pre_rename":
            _record_incident(
                root,
                trial_id=trial_id,
                token=token,
                reason="simulated_pre_rename_crash",
                executor_invocations=invocations,
            )
            _remove_staging(stage)
            raise SimulatedTrialCrash("simulated crash before atomic trial materialization")
        if final.exists():
            raise TrialBundleExists(f"trial already materialized: {trial_id}")
        # Keep the staging directory owner-writable through the same-filesystem
        # rename.  macOS rejects renaming a read-only source directory even
        # when both parents are writable.  The files themselves are already
        # immutable; immediately seal the published directory before its
        # parent is fsynced and before it is returned as authoritative.
        os.rename(stage, final)
        os.chmod(final, 0o555)
        _fsync_directory(root)
        if crash_at == "post_rename":
            raise SimulatedTrialCrash("simulated crash after materialization and before governance")
        return recover_trial_bundle(root, trial_id)
    except SimulatedTrialCrash:
        raise
    except Exception as exc:
        if not final.exists():
            reason = "executor_failed" if isinstance(exc, TrialExecutorError) else "bundle_construction_failed"
            _record_incident(
                root,
                trial_id=trial_id,
                token=token,
                reason=reason,
                executor_invocations=invocations,
            )
            _remove_staging(stage)
        raise
