# Acceptance

Tick each line after you have checked it. The dry-run path needs Python 3, PyYAML, and bash. Docker Compose v2 is for the optional live start.

## Package

- [ ] `README.md` states purpose, inputs, steps, acceptance, boundaries, and requirements
- [ ] `README.zh.md` states 目的、输入、步骤、验收、边界、要求
- [ ] `LICENSE` is the MIT License and `CHANGELOG.md` lists 1.0.0

## Fault coverage

- [ ] Fault class 1 is present: a container or Compose service does not stay up, or becomes unhealthy (`lab/01-container-wont-start/`)
- [ ] `web-exits` is reported as `container-wont-start` because `nginx -c /etc/nginx/broken.conf` has no volume
- [ ] `web-unhealthy` is reported as `container-unhealthy` because wget requests `/healthz`
- [ ] Fault class 2 is present: the published port fails for curl and wget (`lab/02-port-connectivity/`)
- [ ] The broken port mapping is `127.0.0.1:18082:8080` while nginx listens on 80

## Check script

- [ ] `bash check/diagnose.sh` runs as `--dry-run` with no extra flag (`mode=dry-run`)
- [ ] Dry-run prints `writes=none` and creates no file under the host
- [ ] Dry-run on the broken labs exits non-zero (`2`) and names both fault classes
- [ ] Dry-run on the `compose.fixed.yaml` files prints `faults=0` and `result=OK` and exits `0`
- [ ] `bash demo/run-demo.sh` prints `demo_result=OK` and exits `0`

## Safety

- [ ] Lab hostnames use `lab.example.com` and published ports use `127.0.0.1`
- [ ] The tree has no customer IP, customer mailbox, or credential material
- [ ] Check scripts do not run `docker system prune` and do not delete host data
- [ ] A failed check exits non-zero and leaves the host unchanged
- [ ] `bash tests/run_tests.sh` finishes with `tests/RESULTS.md` ending in `FAILS=0`
