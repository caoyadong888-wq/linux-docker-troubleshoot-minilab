#!/usr/bin/env bash
# One successful minilab pass: broken labs report faults, fixed labs are clean.
# Stdout is the command record. The script writes nothing under the package.

set -u
export LC_ALL=C

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

set +e
out1=$(bash "$ROOT/check/diagnose.sh" --dry-run)
ec1=$?
out2=$(bash "$ROOT/check/diagnose.sh" --dry-run \
  --compose "$ROOT/lab/01-container-wont-start/compose.fixed.yaml" \
  --compose "$ROOT/lab/02-port-connectivity/compose.fixed.yaml")
ec2=$?
set -e

printf '%s\n' "command=bash check/diagnose.sh --dry-run" "exit=${ec1}"
printf '%s\n' "$out1"
printf '%s\n' \
  "command=bash check/diagnose.sh --dry-run --compose lab/01-container-wont-start/compose.fixed.yaml --compose lab/02-port-connectivity/compose.fixed.yaml" \
  "exit=${ec2}"
printf '%s\n' "$out2"

if [[ "$ec1" -ne 0 && "$ec2" -eq 0 ]]; then
  printf '%s\n' "demo_result=OK"
  exit 0
fi

printf '%s\n' "demo_result=FAIL"
exit 1
