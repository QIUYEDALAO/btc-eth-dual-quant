#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
      SUDO="sudo"
    else
      SUDO=""
    fi
    $SUDO apt-get update
    $SUDO apt-get install -y python3 python3-pip
  else
    echo "python3 is required for validation." >&2
    exit 1
  fi
fi

if ! python3 -m pip --version >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
      SUDO="sudo"
    else
      SUDO=""
    fi
    $SUDO apt-get update
    $SUDO apt-get install -y python3-pip
  else
    echo "python3 pip is required for validation." >&2
    exit 1
  fi
fi

mkdir -p .deps
python3 -m pip install --upgrade --target .deps "pydantic>=2.0" "duckdb>=1.0" "PyYAML>=6.0"
echo "Python validation dependencies installed into ignored .deps/."
