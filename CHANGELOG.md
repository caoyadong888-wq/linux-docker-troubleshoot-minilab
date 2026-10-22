# Changelog

## 1.0.0 - 2026-10-22

- Initial release of the Linux and Docker troubleshoot minilab.
- Scenario `lab/01-container-wont-start/`: nginx exits on a missing config, and a second service becomes unhealthy because its healthcheck requests `/healthz`.
- Scenario `lab/02-port-connectivity/`: the published container port is 8080 while nginx listens on 80, so curl and wget to `127.0.0.1` fail.
- `check/diagnose.sh` defaults to `--dry-run`, prints a report, and writes no host files.
- Fixed Compose files, EXPECTED and FIX notes, a demo transcript, and pytest coverage.
