# Demo record

One dry-run pass from the package root. Docker is optional. The checker reads the lab files and writes nothing.

## Commands

```bash
bash check/diagnose.sh --dry-run
bash check/diagnose.sh --dry-run \
  --compose lab/01-container-wont-start/compose.fixed.yaml \
  --compose lab/02-port-connectivity/compose.fixed.yaml
bash demo/run-demo.sh
```

`run-demo.sh` runs those two checks. The broken labs exit non-zero. The fixed labs exit `0`. The script then prints `demo_result=OK` and itself exits `0`.

## Stdout

The full stdout of `bash demo/run-demo.sh` is in `captured-output.txt`.

You should see:

- `mode=dry-run` and `writes=none`
- `class=container-wont-start` for `web-exits`
- `class=container-unhealthy` for `web-unhealthy`
- `class=port-connectivity` with probe `http://127.0.0.1:18082/`
- a second report with `faults=0` and `result=OK`
- the last line `demo_result=OK`

## After the dry-run

Read `lab/01-container-wont-start/FIX.md` and `lab/02-port-connectivity/FIX.md`. When Docker Compose v2 is installed, the FIX files include the optional `docker compose up` and `curl` commands. Those commands are not part of this captured dry-run.
