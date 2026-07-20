#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_CMD="${PYTHON:-python3}"
MANIFEST="$ROOT/config/u04_u24_history_archive_v1.json"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/u04-u24-replay.XXXXXX")"
SNAPSHOT_ROOT="$SCRATCH/source-snapshot"

cleanup() {
  git -C "$ROOT" worktree remove --force "$SCRATCH/worktree" >/dev/null 2>&1 || true
  chmod -R u+w "$SCRATCH" >/dev/null 2>&1 || true
  rm -rf -- "$SCRATCH"
}
trap cleanup EXIT

"$PY_CMD" "$ROOT/scripts/u04_u24_history_archive_check.py"

snapshot_records() {
  "$PY_CMD" - "$MANIFEST" <<'PY'
import json, sys
for item in json.load(open(sys.argv[1], encoding="utf-8"))["replay_source_snapshots"]:
    print(f"{item['path']}\t{item['bytes']}\t{item['sha256']}")
PY
}

verify_snapshot_set() {
  local base="$1" label="$2" relative expected_size expected_hash actual_size actual_hash
  while IFS=$'\t' read -r relative expected_size expected_hash; do
    [[ -f "$base/$relative" ]] || { echo "$label missing: $relative" >&2; return 1; }
    actual_size="$(wc -c < "$base/$relative" | tr -d ' ')"
    actual_hash="$($PY_CMD - "$base/$relative" <<'PY'
import hashlib, pathlib, sys
print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
)"
    [[ "$actual_size" == "$expected_size" ]] || { echo "$label size changed: $relative" >&2; return 1; }
    [[ "$actual_hash" == "$expected_hash" ]] || { echo "$label hash changed: $relative" >&2; return 1; }
  done < <(snapshot_records)
}

mkdir -p "$SNAPSHOT_ROOT"
while IFS=$'\t' read -r relative expected_size expected_hash; do
  mkdir -p "$SNAPSHOT_ROOT/$(dirname "$relative")"
  cp -p "$ROOT/$relative" "$SNAPSHOT_ROOT/$relative"
done < <(snapshot_records)
verify_snapshot_set "$ROOT" "root snapshot"
verify_snapshot_set "$SNAPSHOT_ROOT" "temporary snapshot"
find "$SNAPSHOT_ROOT" -type f -exec chmod a-w {} +
find "$SNAPSHOT_ROOT" -type d -exec chmod a-w {} +

if [[ "${ARCHIVE_REPLAY_SNAPSHOT_PROBE_ONLY:-0}" == "1" ]]; then
  probe_path="$(snapshot_records | head -1 | cut -f1)"
  if printf 'mutation-probe' >> "$SNAPSHOT_ROOT/$probe_path" 2>/dev/null; then
    verify_snapshot_set "$SNAPSHOT_ROOT" "temporary snapshot"
    echo "mutation unexpectedly escaped final hash Gate" >&2
    exit 1
  fi
  verify_snapshot_set "$SNAPSHOT_ROOT" "temporary snapshot"
  verify_snapshot_set "$ROOT" "root snapshot"
  echo "archive replay snapshot write blocked PASS"
  exit 0
fi

"$PY_CMD" - "$MANIFEST" <<'PY' | while IFS=$'\t' read -r commit validator; do
import json, sys
for commit, validator in json.load(open(sys.argv[1], encoding="utf-8"))["replay_stages"]:
    print(f"{commit}\t{validator}")
PY
  echo "==> replay $commit $validator"
  verify_snapshot_set "$ROOT" "root snapshot before $commit"
  verify_snapshot_set "$SNAPSHOT_ROOT" "temporary snapshot before $commit"
  git -C "$ROOT" worktree add --detach "$SCRATCH/worktree" "$commit" >/dev/null
  if [[ -d "$SNAPSHOT_ROOT/storage/raw" && ! -e "$SCRATCH/worktree/storage/raw" ]]; then
    mkdir -p "$SCRATCH/worktree/storage"
    ln -s "$SNAPSHOT_ROOT/storage/raw" "$SCRATCH/worktree/storage/raw"
  fi
  git -C "$SCRATCH/worktree" diff --exit-code --quiet
  [[ -z "$(git -C "$SCRATCH/worktree" status --porcelain --untracked-files=all)" ]]
  (
    cd "$SCRATCH/worktree"
    export PYTHONPATH="$ROOT/.deps:$SCRATCH/worktree/src"
    export PYTHON="$PY_CMD"
    bash "$validator"
  )
  git -C "$SCRATCH/worktree" diff --exit-code --quiet
  [[ -z "$(git -C "$SCRATCH/worktree" status --porcelain --untracked-files=all)" ]]
  verify_snapshot_set "$SNAPSHOT_ROOT" "temporary snapshot after $commit"
  verify_snapshot_set "$ROOT" "root snapshot after $commit"
  git -C "$ROOT" worktree remove --force "$SCRATCH/worktree" >/dev/null
done

verify_snapshot_set "$SNAPSHOT_ROOT" "temporary snapshot final"
verify_snapshot_set "$ROOT" "root snapshot final"
echo "u04_u24_history_archive_replay PASS"
