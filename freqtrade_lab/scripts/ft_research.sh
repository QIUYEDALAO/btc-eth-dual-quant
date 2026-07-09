#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
bash scripts/ft_no_live_guard.sh

if [[ "$#" -lt 1 ]]; then
  echo "Usage: $0 {download-data|list-data|backtesting|lookahead-analysis|recursive-analysis|webserver} [arguments...]" >&2
  exit 2
fi

research_command="$1"
shift

run_checked() {
  local output
  local exit_code
  set +e
  output="$(docker compose run --rm freqtrade "$@" 2>&1)"
  exit_code=$?
  set -e
  printf '%s\n' "$output"
  if [[ "$exit_code" -ne 0 ]]; then
    return "$exit_code"
  fi
  if printf '%s\n' "$output" | grep -E 'Configuration error|CRITICAL|Traceback \(most recent call last\)' >/dev/null; then
    return 1
  fi
}

case "$research_command" in
  download-data|list-data|backtesting|lookahead-analysis|recursive-analysis)
    run_checked "$research_command" "$@"
    ;;
  webserver)
    echo "Freqtrade research WebUI will bind only to 127.0.0.1:8080."
    exec docker compose run --rm -p 127.0.0.1:8080:8080 freqtrade webserver "$@"
    ;;
  *)
    echo "Rejected non-research Freqtrade command: $research_command" >&2
    exit 2
    ;;
esac
