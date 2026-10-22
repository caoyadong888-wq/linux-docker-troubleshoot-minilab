#!/usr/bin/env bash
# Run the pytest suite and require tests/RESULTS.md to end with FAILS=0.

set -u
export LC_ALL=C
export PYTHONDONTWRITEBYTECODE=1

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

python3 -m pytest -q -p no:cacheprovider tests
code=$?

if [[ ! -f tests/RESULTS.md ]]; then
  echo "error=missing tests/RESULTS.md" >&2
  exit 1
fi

last=$(tail -n 1 tests/RESULTS.md)
printf '%s\n' "results_last_line=${last}"
if [[ "$last" != "FAILS=0" ]]; then
  echo "error=RESULTS.md did not end with FAILS=0" >&2
  exit 1
fi

exit "$code"
