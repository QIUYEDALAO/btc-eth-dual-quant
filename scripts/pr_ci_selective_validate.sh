#!/usr/bin/env bash
set -euo pipefail

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH=".:.deps:src${PYTHONPATH:+:$PYTHONPATH}"
BASE_SHA="${PR_BASE_SHA:-$(git merge-base HEAD origin/main)}"

git cat-file -e "${BASE_SHA}^{commit}"
CHANGED_FILES="$(git diff --name-only "$BASE_SHA" HEAD)"
CHANGED_COUNT="$(printf '%s\n' "$CHANGED_FILES" | sed '/^$/d' | wc -l | tr -d ' ')"

echo "PR selective Gate: ${CHANGED_COUNT} changed files"
bash scripts/project_validate.sh
"$PY_CMD" -m compileall -q src scripts
"$PY_CMD" scripts/m0_secret_scan.py
git diff --check "$BASE_SHA" HEAD

SELECTED_VALIDATORS=""
workflow_body_changed() {
  local workflow_path="$1"
  local diff_line trimmed
  while IFS= read -r diff_line; do
    case "$diff_line" in
      "+++"*|"---"*|"@@"*) continue ;;
      +*|-*) ;;
      *) continue ;;
    esac
    trimmed="${diff_line:1}"
    trimmed="${trimmed#"${trimmed%%[![:space:]]*}"}"
    case "$trimmed" in
      ""|"on:"|"on: ["*|"push:"|"pull_request:"|"workflow_dispatch:"|"branches: [main]") ;;
      *) return 0 ;;
    esac
  done < <(git diff --unified=0 "$BASE_SHA" HEAD -- "$workflow_path")
  return 1
}

while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  if [[ "$path" == scripts/*_validate.sh && "$path" != scripts/project_validate.sh && "$path" != scripts/pr_ci_selective_validate.sh ]]; then
    SELECTED_VALIDATORS="${SELECTED_VALIDATORS}${path}"$'\n'
  fi
  if [[ "$path" == .github/workflows/*.yml && -f "$path" ]] && workflow_body_changed "$path"; then
    while IFS= read -r validator; do
      if [[ -n "$validator" && -f "$validator" && "$validator" != scripts/project_validate.sh && "$validator" != scripts/pr_ci_selective_validate.sh ]]; then
        SELECTED_VALIDATORS="${SELECTED_VALIDATORS}${validator}"$'\n'
      fi
    done < <(rg -o 'scripts/[A-Za-z0-9_./-]+_validate\.sh' "$path" | sort -u || true)
  fi
done <<< "$CHANGED_FILES"

if printf '%s\n' "$CHANGED_FILES" | rg -q '^\.github/workflows/'; then
  "$PY_CMD" scripts/ci_pr_trigger_policy_check.py
fi

SELECTED_VALIDATORS="$(printf '%s' "$SELECTED_VALIDATORS" | sed '/^$/d' | sort -u)"
if [[ -z "$SELECTED_VALIDATORS" ]]; then
  echo "No stage-specific validator changed; project Gate is sufficient."
else
  while IFS= read -r validator; do
    echo "==> selected validator: $validator"
    bash "$validator"
  done <<< "$SELECTED_VALIDATORS"
fi

echo "pr_ci_selective_validate PASS"
