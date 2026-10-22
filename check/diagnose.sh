#!/usr/bin/env bash
# Read-only minilab diagnose. Default is dry-run (no flag required).
# Prints a report on stdout. Does not write host files and does not
# start, stop, or delete containers.

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

if [[ ! -f "$ROOT/check/diagnose.py" ]]; then
  echo "error=missing diagnose.py" >&2
  exit 1
fi

exec python3 "$ROOT/check/diagnose.py" "$@"
