#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_CMD="${PYTHON:-python3}"
MANIFEST="$ROOT/config/u04_u24_history_archive_v1.json"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/u04-u24-replay.XXXXXX")"

cleanup() {
  git -C "$ROOT" worktree remove --force "$SCRATCH/worktree" >/dev/null 2>&1 || true
  rm -rf -- "$SCRATCH"
}
trap cleanup EXIT

"$PY_CMD" "$ROOT/scripts/u04_u24_history_archive_check.py"

"$PY_CMD" - "$MANIFEST" <<'PY' | while IFS=$'\t' read -r commit validator; do
import json, sys
for commit, validator in json.load(open(sys.argv[1], encoding="utf-8"))["replay_stages"]:
    print(f"{commit}\t{validator}")
PY
  echo "==> replay $commit $validator"
  git -C "$ROOT" worktree add --detach "$SCRATCH/worktree" "$commit" >/dev/null
  # U-15+ validators bind frozen raw archive bytes. The store is intentionally
  # gitignored, so exact-tree replay mounts the same local source read-only.
  if [[ -d "$ROOT/storage/raw" && ! -e "$SCRATCH/worktree/storage/raw" ]]; then
    mkdir -p "$SCRATCH/worktree/storage"
    ln -s "$ROOT/storage/raw" "$SCRATCH/worktree/storage/raw"
  fi
  (
    cd "$SCRATCH/worktree"
    export PYTHONPATH="$ROOT/.deps:$SCRATCH/worktree/src"
    export PYTHON="$PY_CMD"
    bash "$validator"
  )
  git -C "$ROOT" worktree remove --force "$SCRATCH/worktree" >/dev/null
done

echo "u04_u24_history_archive_replay PASS"
