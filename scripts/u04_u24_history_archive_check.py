#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/u04_u24_history_archive_v1.json"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    base = data["base_commit"]
    terminal = data["terminal_commit"]
    reachability = data["reachability_commit"]
    commits = git("rev-list", "--reverse", f"{base}..{terminal}").splitlines()
    commit_digest = hashlib.sha256(("\n".join(commits) + "\n").encode()).hexdigest()
    if len(commits) != data["mainline_commit_count"]:
        failures.append("mainline commit count changed")
    if commit_digest != data["mainline_commit_list_sha256"]:
        failures.append("mainline commit identity changed")
    terminal_tree = git("rev-parse", f"{terminal}^{{tree}}")
    reachability_tree = git("rev-parse", f"{reachability}^{{tree}}")
    if terminal_tree != data["terminal_tree"] or reachability_tree != terminal_tree:
        failures.append("reachability merge changed the historical tree")
    parents = git("show", "-s", "--format=%P", reachability).split()
    expected_parents = [terminal, *data["anchored_exact_heads"]]
    if parents != expected_parents:
        failures.append("anchored exact-head parent set changed")
    patterns = "(u|U)(0[4-9]|1[0-9]|2[0-4])|STRATEGY_TRIAL_LEDGER|PROJECT_STATE|PROJECT_LEDGER|NEXT_ACTION|AGENTS|PROJECT_EXECUTION_CHECKLIST"
    listing = subprocess.check_output(
        ["bash", "-lc", f"git ls-tree -r {terminal} -- config reports scripts tests STRATEGY_TRIAL_LEDGER.yaml PROJECT_STATE.yaml PROJECT_LEDGER.md NEXT_ACTION.md AGENTS.md PROJECT_EXECUTION_CHECKLIST.md | rg '{patterns}' | sort"],
        cwd=ROOT,
    )
    lines = listing.splitlines()
    if len(lines) != data["evidence_path_count"]:
        failures.append("historical evidence path count changed")
    if hashlib.sha256(listing).hexdigest() != data["evidence_tree_listing_sha256"]:
        failures.append("historical evidence tree listing changed")
    for short_commit, validator in data["replay_stages"]:
        try:
            git("rev-parse", f"{short_commit}^{{commit}}")
            git("cat-file", "-e", f"{short_commit}:{validator}")
        except subprocess.CalledProcessError:
            failures.append(f"replay target unavailable: {short_commit}:{validator}")
    if data.get("tree_changed_by_reachability_merge") is not False or data.get("historical_evidence_mutation_authorized") is not False:
        failures.append("archive permissions changed")
    if failures:
        print("u04_u24_history_archive_check FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("u04_u24_history_archive_check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
