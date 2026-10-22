# Linux / Docker troubleshoot minilab

## Purpose

A small, repeatable lab for two Docker troubleshooting classes on one Linux machine:

1. A container or Compose service exits on startup (`container-wont-start`), and a second service stays up and becomes unhealthy (`container-unhealthy`).
2. A published port looks open in Compose while curl and wget to `127.0.0.1` fail (`port-connectivity`), because the mapping points at the wrong container port.

`check/diagnose.sh` reads the lab files and prints the class, the probe, and the expected symptom. The default mode is `--dry-run`. It writes nothing and it does not start Docker.

## Inputs

- This package, unpacked, as the working directory.
- A Linux shell with bash and Python 3.
- PyYAML for the checker (`python3 -m pip install -r requirements.txt`).
- Docker Compose v2 when you want to start the lab. The dry-run path does not need a daemon.
- The broken files are the scenarios:
  - `lab/01-container-wont-start/compose.yaml`
  - `lab/02-port-connectivity/compose.yaml`
- The repaired files are `compose.fixed.yaml` next to each broken file.

Hostnames in the lab are `web-exits.lab.example.com`, `web-unhealthy.lab.example.com`, and `web.lab.example.com`. Published ports are `127.0.0.1:18081`, `127.0.0.1:18083`, and `127.0.0.1:18082`.

## Steps

1. `cd` to the package root (the directory that contains this README).
2. Read `lab/01-container-wont-start/EXPECTED.md` and `lab/02-port-connectivity/EXPECTED.md`. Start a scenario with Docker Compose v2, or stay on the dry-run path:

   ```bash
   bash check/diagnose.sh --dry-run
   ```

3. Run the checker and compare the report with the EXPECTED notes. Broken labs exit `2`.

   ```bash
   bash check/diagnose.sh
   ```

   With no flag, the mode is still `--dry-run`.

4. Apply the edits in each `FIX.md` (or pass the shipped `compose.fixed.yaml`) and run the checker again:

   ```bash
   bash check/diagnose.sh --dry-run \
     --compose lab/01-container-wont-start/compose.fixed.yaml \
     --compose lab/02-port-connectivity/compose.fixed.yaml
   bash demo/run-demo.sh
   ```

   The fixed run exits `0`. `demo/run-demo.sh` prints `demo_result=OK`.

Optional live start, after Docker Compose v2 is installed, is written in each FIX file. Stop a project with `docker compose -f <file> down`.

## Acceptance

Tick `ACCEPTANCE.md` after you walk the steps. The package is done when all of these are true:

- Both READMEs state purpose, inputs, steps, acceptance, boundaries, and requirements.
- Scenario 01 covers a container that exits and a container that becomes unhealthy.
- Scenario 02 covers curl and wget failure on the published port.
- `bash check/diagnose.sh` defaults to dry-run, prints `writes=none`, and writes no host file.
- `bash demo/run-demo.sh` exits `0` and `demo/captured-output.txt` matches its stdout.
- `bash tests/run_tests.sh` leaves `tests/RESULTS.md` ending in `FAILS=0`.
- The tree uses `example.com` and `127.0.0.1` and holds no customer IP, mailbox, or credential.

Exit codes from the checker:

| Exit | Meaning |
| --- | --- |
| 0 | The selected files have no fault. |
| 1 | Usage error, unreadable file, refused live target, or live Docker is missing. |
| 2 | One or more faults. The host is unchanged. |

## Boundaries

- Lab names stay on `*.example.com`. Published ports stay on `127.0.0.1`. Do not point the lab at a production host, and do not change production configuration from these scripts.
- The sample image is the public Docker Official `nginx:1.27-alpine`. The lab does not require a paid registry and it does not log in to one.
- Check scripts print to stdout. They do not write under `/etc`, `/root`, `/home`, or `/var`. They do not run `docker system prune`, including `docker system prune -a`, and they do not delete images or volumes.
- `--live` is opt-in. It may run `docker compose ps` and `curl` to `http://127.0.0.1` only. It refuses any other probe address. It does not run `up`, `down`, `pull`, or `rm`.
- A fault or a usage error exits non-zero and leaves the machine as it was.
- Dry-run is the default, so a machine without Docker can still finish the demo and the tests.

## Requirements

- Linux with bash.
- Python 3.9 or newer, and PyYAML 6 (`requirements.txt`).
- Docker Engine and Docker Compose v2 only for the optional container start in the FIX files. Check the upstream install notes for your distribution.
- `curl` is used by the optional `--live` port probe and by the FIX examples. `wget` is the healthcheck binary inside `nginx:1.27-alpine`.
- No root rights for the dry-run. The checker does not use sudo.
- Free host ports `18081`, `18082`, and `18083` when you start the lab.

## Layout

- `README.md`, `README.zh.md` — this guide, in English and Chinese
- `ACCEPTANCE.md` — checklist
- `lab/01-container-wont-start/` — broken Compose, fixed Compose, EXPECTED, FIX
- `lab/02-port-connectivity/` — broken Compose, fixed Compose, EXPECTED, FIX
- `check/diagnose.sh`, `check/diagnose.py` — read-only checker, dry-run by default
- `demo/run-demo.sh`, `demo/demo.md`, `demo/captured-output.txt` — one successful command record
- `tests/` — pytest suite, `run_tests.sh`, and `RESULTS.md`
- `LICENSE` — MIT
- `CHANGELOG.md` — 1.0.0
- `requirements.txt` — PyYAML

## Quick start

```bash
python3 -m pip install -r requirements.txt
bash check/diagnose.sh --dry-run
bash demo/run-demo.sh
bash tests/run_tests.sh
```

## Scenarios

### 01 · Container won't start / unhealthy (`lab/01-container-wont-start/`)

- **Symptom:** `web-exits` exits right away; logs show nginx `emerg` opening `/etc/nginx/broken.conf`. `web-unhealthy` stays up but `docker compose ps` shows `unhealthy`.
- **Diagnose:** `bash check/diagnose.sh --dry-run`. It reports `container-wont-start` and `container-unhealthy` (`result=FAULT`, exit 2). Details are in `EXPECTED.md`.
- **Fix:** remove the bad `command:` override, and point the healthcheck at `http://127.0.0.1/` instead of `/healthz`. See `FIX.md` and `compose.fixed.yaml`.
- **Verify:** `bash check/diagnose.sh --dry-run --compose lab/01-container-wont-start/compose.fixed.yaml` should give `faults=0`, `result=OK`, exit 0.

### 02 · Port connectivity (`lab/02-port-connectivity/`)

- **Symptom:** the container is `Up`, but `curl http://127.0.0.1:18082/` is refused.
- **Diagnose:** the mapping `127.0.0.1:18082:8080` targets a port nothing listens on, because nginx listens on 80. The checker reports `port-connectivity`.
- **Fix:** change the mapping to `127.0.0.1:18082:80`. See `FIX.md`.
- **Verify:** `bash check/diagnose.sh --dry-run --compose lab/02-port-connectivity/compose.fixed.yaml` should give `faults=0`, `result=OK`. If you run it live, `curl` exits 0.

## Paid help / 可付费协助

Fixed-price remote Linux/Docker troubleshooting (text-only by default; no remote desktop unless agreed).

| Tier | Scope | Price |
|------|--------|-------|
| Single clear fault | One container won't start, one published port dead, one Nginx 502 | USD $15 / ¥99 |
| Linked services | Compose + reverse proxy / multi-container | USD $30 / ¥199 |
| Complex multi-round | Several services, iterative diagnosis | USD $45 / ¥299 |

**How to order:** email **caoyadong888@gmail.com** with the symptom and redacted logs/config. Free quick look, then confirm price before work.

**Deliverables:** root-cause note, step-by-step fix, and how to verify.

**Not included:** unlimited support, long-term ops retainers, guaranteed fix of third-party outages, or any circumvention / unlawful use.

This public lab is the sample. Starter test rates for one clear problem; larger scope is quoted first.
