# EXPECTED · container exits or unhealthy

Project name: `minilab-wont-start`.

## web-exits

- Command is `nginx -c /etc/nginx/broken.conf`.
- That path is not in the official image and the file has no volume.
- The container process exits. `docker compose ps` shows `Exited` (or a restart loop only if you add a restart policy; this file has none).
- Logs contain an nginx emerg line about opening `/etc/nginx/broken.conf`.
- Class id: `container-wont-start`.

## web-unhealthy

- The image command is the stock nginx entrypoint, so the process stays up.
- The healthcheck runs `wget` against `http://127.0.0.1/healthz`.
- Stock nginx does not serve `/healthz` (the response is 404).
- After the retries, `docker compose ps` shows the container as `unhealthy`.
- Class id: `container-unhealthy`.

## Checker

From the package root, `bash check/diagnose.sh --dry-run` reports both services as `result=FAULT` and exits `2`. The command prints the report and writes no file.
