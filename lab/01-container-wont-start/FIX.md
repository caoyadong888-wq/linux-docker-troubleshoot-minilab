# FIX · container exits or unhealthy

Compare `compose.yaml` with `compose.fixed.yaml` in this directory. Apply the same two edits to your copy.

## web-exits

Remove the `command:` list. The Docker Official `nginx:1.27-alpine` image already starts nginx with `/etc/nginx/nginx.conf` and `daemon off` in its entrypoint. A missing `-c` path is what makes the process exit.

## web-unhealthy

Change the healthcheck URL from `http://127.0.0.1/healthz` to `http://127.0.0.1/`. Stock nginx serves `/` with status 200, so wget succeeds and the container becomes healthy.

A larger repair is to mount a config that defines `location /healthz` and returns 200. This minilab ships the probe change, which is the smaller edit.

## Check again

```bash
bash check/diagnose.sh --dry-run --compose lab/01-container-wont-start/compose.fixed.yaml
```

Expect `faults=0`, `result=OK`, and exit `0`.

## Optional live start

```bash
docker compose -f lab/01-container-wont-start/compose.fixed.yaml up -d
docker compose -f lab/01-container-wont-start/compose.fixed.yaml ps
curl -fsS --max-time 3 http://127.0.0.1:18081/
curl -fsS --max-time 3 http://127.0.0.1:18083/
docker compose -f lab/01-container-wont-start/compose.fixed.yaml down
```

`down` removes this project’s containers and network. It does not prune unused images or volumes on the host.
