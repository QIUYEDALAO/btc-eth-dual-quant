#!/usr/bin/env python3
"""Run the frozen V4 public qualification cold, warm and worker variants."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

from btc_eth_dual_quant.data.liquid_universe import canonical_hash
from btc_eth_dual_quant.data.liquid_universe_artifacts import write_manifest
from btc_eth_dual_quant.data.liquid_universe_pipeline import artifact_set_hash
from btc_eth_dual_quant.data.lifecycle_artifacts import V4_MANIFEST_TYPES
from scripts.liquid_universe_public_run import DEFAULT_RAW, ROOT
from scripts.liquid_universe_v4_public_run import run


REQUIRED_SOURCE_FREEZE_HASH = "c86310f8a734da214e4119268af874db6398d1b2552426c22431f97d1cffec6c"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze_sources(raw_root: Path) -> dict:
    v3_source = json.loads(
        (ROOT / "reports/m0/evidence/liquid_universe_v3/source_manifest.json").read_text(encoding="utf-8")
    )["content"]
    rows = []
    for source in v3_source:
        path = raw_root / Path(source["canonical_key"]).relative_to("data/spot")
        if not path.exists():
            raise ValueError(f"source freeze missing archive: {source['canonical_key']}")
        digest = file_sha256(path)
        if digest != source["sha256"]:
            raise ValueError(f"source_revision_blocked:{source['canonical_key']}")
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"source CRC failure:{source['canonical_key']}:{bad}")
        rows.append({
            "canonical_key": source["canonical_key"],
            "sha256": digest,
            "byte_size": path.stat().st_size,
        })
    content = {
        "range": {"start": "2020-01", "end": "2026-06"},
        "archive_count": len(rows),
        "archives": rows,
        "v3_source_manifest_hash": canonical_hash(v3_source),
        "crc_failures": 0,
        "source_revisions": 0,
    }
    return {
        "schema_version": 4,
        "manifest_type": "liquid_universe_v4_source_freeze",
        "content": content,
        "content_hash": canonical_hash(content),
    }


def assert_three_way(builds: dict, reports: dict, diffs: dict) -> None:
    if set(builds) != {"cold", "warm", "worker"}:
        raise ValueError("cold/warm/worker builds are required")
    for name in ("warm", "worker"):
        if artifact_set_hash(builds[name]) != artifact_set_hash(builds["cold"]):
            raise ValueError(f"{name} artifact-set mismatch")
        mismatches = [
            key for key in sorted(V4_MANIFEST_TYPES)
            if builds[name][key]["content_hash"] != builds["cold"][key]["content_hash"]
        ]
        if mismatches:
            raise ValueError(f"{name} manifest mismatch: {','.join(mismatches)}")
        if reports[name].read_bytes() != reports["cold"].read_bytes():
            raise ValueError(f"{name} qualification report mismatch")
        if diffs[name].read_bytes() != diffs["cold"].read_bytes():
            raise ValueError(f"{name} V3/V4 diff mismatch")


def _write_json(path: Path, document: dict) -> None:
    payload = (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    _atomic_write_bytes(path, payload)


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def render_bound_report(
    base_report: bytes,
    records: dict[str, dict],
    *,
    source_freeze_hash: str,
    determinism_status: str,
) -> bytes:
    suffix = ["", "## Build Hashes", ""]
    suffix.extend(f"- {name}: `{records[name]['artifact_set_hash']}`" for name in records)
    suffix.extend([
        f"- Source freeze: `{source_freeze_hash}`",
        f"- Determinism: {determinism_status}",
        "",
    ])
    return base_report.rstrip(b"\n") + b"\n" + "\n".join(suffix).encode("utf-8")


def verify_report_binding(report_path: Path, run_manifest: dict) -> str:
    actual = file_sha256(report_path)
    records = run_manifest.get("content", {}).get("builds", {})
    if not records:
        raise ValueError("run manifest contains no report binding")
    mismatches = [name for name, record in records.items() if record.get("qualification_report_sha256") != actual]
    if mismatches:
        raise ValueError(f"qualification report binding mismatch: {','.join(sorted(mismatches))}")
    return actual


def _load_completed_build(work_root: Path, name: str) -> tuple[dict, Path, Path] | None:
    build_dir = work_root / name
    report = work_root / f"{name}.md"
    diff = work_root / f"{name}-v3-v4.md"
    paths = [build_dir / f"{manifest}.json" for manifest in V4_MANIFEST_TYPES]
    if not report.exists() or not diff.exists() or not all(path.exists() for path in paths):
        return None
    artifacts = {}
    for path in paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        unsigned = {key: value for key, value in document.items() if key != "content_hash"}
        if document.get("content_hash") != canonical_hash(unsigned):
            raise ValueError(f"resume artifact hash mismatch: {path}")
        artifacts[path.stem] = document
    return artifacts, report, diff


def execute(
    *, raw_root: Path, work_root: Path, evidence_dir: Path, report_path: Path,
    diff_report_path: Path, workers_cold: int, workers_warm: int, workers_variant: int,
    resume: bool = False,
) -> dict:
    if not resume:
        shutil.rmtree(work_root, ignore_errors=True)
    source_before = freeze_sources(raw_root)
    if source_before["content"].get("archive_count") != 27_736:
        raise ValueError("source freeze archive count drift")
    if source_before.get("content_hash") != REQUIRED_SOURCE_FREEZE_HASH:
        raise ValueError("source freeze content hash drift before requalification")
    builds: dict[str, dict] = {}
    reports: dict[str, Path] = {}
    diffs: dict[str, Path] = {}
    workers = {"cold": workers_cold, "warm": workers_warm, "worker": workers_variant}
    for name in ("cold", "warm", "worker"):
        completed_build = _load_completed_build(work_root, name) if resume else None
        if completed_build is not None:
            builds[name], reports[name], diffs[name] = completed_build
            print(f"build={name} status=resumed artifact_set={artifact_set_hash(builds[name])}", flush=True)
            continue
        build_dir = work_root / name
        reports[name] = work_root / f"{name}.md"
        diffs[name] = work_root / f"{name}-v3-v4.md"
        print(f"build={name} workers={workers[name]} status=started", flush=True)
        builds[name] = run(
            raw_root=raw_root, evidence_dir=build_dir, end_month="2026-06",
            report_path=reports[name], diff_report_path=diffs[name], offline=True,
            workers=workers[name], verify_remote_registry=False,
        )
        summary = builds[name]["qualification_summary"]["content"]
        print(f"build={name} status={summary['status']} artifact_set={artifact_set_hash(builds[name])}", flush=True)
        if name == "cold" and summary["status"] != "pass":
            print("builds=warm,worker status=not_run_due_fail_closed_cold_block", flush=True)
            break

    completed = set(builds) == {"cold", "warm", "worker"}
    if completed:
        assert_three_way(builds, reports, diffs)
    source_after = freeze_sources(raw_root)
    if source_after.get("content_hash") != REQUIRED_SOURCE_FREEZE_HASH:
        raise ValueError("source freeze content hash drift during requalification")
    if source_before["content_hash"] != source_after["content_hash"]:
        raise ValueError("source freeze drift during requalification")

    cold = builds["cold"]
    summary = cold["qualification_summary"]["content"]
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for name in sorted(V4_MANIFEST_TYPES):
        shutil.copyfile(work_root / "cold" / f"{name}.json", evidence_dir / f"{name}.json")
    shutil.copyfile(diffs["cold"], diff_report_path)
    write_manifest(evidence_dir / "source_freeze_manifest.json", source_before)

    records = {
        name: {
            "workers": workers[name],
            "artifact_set_hash": artifact_set_hash(builds[name]),
            "manifest_hashes": {key: builds[name][key]["content_hash"] for key in sorted(builds[name])},
            "build_qualification_report_sha256": file_sha256(reports[name]),
            "v3_v4_diff_sha256": file_sha256(diffs[name]),
        }
        for name in builds
    }
    determinism_status = "pass" if completed else "not_run_due_fail_closed_cold_block"
    final_report = render_bound_report(
        reports["cold"].read_bytes(),
        records,
        source_freeze_hash=source_before["content_hash"],
        determinism_status=determinism_status,
    )
    _atomic_write_bytes(report_path, final_report)
    final_report_sha256 = file_sha256(report_path)
    for record in records.values():
        record["qualification_report_sha256"] = final_report_sha256
    run_content = {
        "status": summary["status"],
        "range": {"start": "2020-01", "end": "2026-06"},
        "source_mode": "frozen_local_only",
        "source_freeze_hash": source_before["content_hash"],
        "builds": records,
        "builds_completed": list(builds),
        "determinism_status": determinism_status,
        "deterministic_mismatches": 0 if completed else None,
        "stop_reasons": [] if completed else summary.get("blockers", []),
        "processing_errors": summary["processing_errors"],
        "unresolved_row_conflicts": summary["unresolved_row_conflicts"],
        "unresolved_lifecycle_rows": summary["unresolved_lifecycle_rows"],
        "epoch_overlaps": summary["epoch_overlaps"],
        "unresolved_gaps": summary["unresolved_gaps"],
        "synthetic_fills": summary["synthetic_fills"],
        "replacement_members": summary["replacement_members"],
        "authorizations": summary["authorizations"],
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    run_manifest = {
        "schema_version": 4,
        "manifest_type": "liquid_universe_v4_requalification_run",
        "content": run_content,
    }
    run_manifest["content_hash"] = canonical_hash(run_manifest)
    _write_json(evidence_dir / "requalification_run_manifest.json", run_manifest)
    verify_report_binding(report_path, run_manifest)
    return run_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--work-root", type=Path, default=ROOT / "storage/logs/liquid_universe_v4_requalification")
    parser.add_argument("--evidence-dir", type=Path, default=ROOT / "reports/m0/evidence/liquid_universe_v4")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V4_QUALIFICATION_REPORT.md")
    parser.add_argument("--diff-report", type=Path, default=ROOT / "reports/m0/LIQUID_SPOT_UNIVERSE_V3_V4_DIFF_REPORT.md")
    parser.add_argument("--workers-cold", type=int, default=16)
    parser.add_argument("--workers-warm", type=int, default=3)
    parser.add_argument("--workers-variant", type=int, default=7)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    document = execute(
        raw_root=args.raw_root, work_root=args.work_root, evidence_dir=args.evidence_dir,
        report_path=args.report, diff_report_path=args.diff_report,
        workers_cold=args.workers_cold, workers_warm=args.workers_warm,
        workers_variant=args.workers_variant, resume=args.resume,
    )
    print(f"status={document['content']['status']} content_hash={document['content_hash']}")
    return 0 if document["content"]["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
