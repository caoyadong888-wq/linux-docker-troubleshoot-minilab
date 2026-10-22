# Lab scenarios

Two Compose projects. Each broken file is the scenario you diagnose. The matching `compose.fixed.yaml` is the repair you compare after the FIX notes.

| Directory | Class | What you observe |
| --- | --- | --- |
| `01-container-wont-start/` | Container exits, and a second service is unhealthy | `web-exits` uses `nginx -c /etc/nginx/broken.conf`. `web-unhealthy` stays up and fails its wget healthcheck for `/healthz`. |
| `02-port-connectivity/` | Published port | Host `127.0.0.1:18082` forwards to container port 8080. The process listens on 80. curl and wget fail. |

Hostnames in the files use `lab.example.com`. Published ports bind `127.0.0.1` only.

Dry-run the checker from the package root:

```bash
bash check/diagnose.sh --dry-run
```

When Docker Compose v2 is installed, start a scenario only after you have read its EXPECTED note:

```bash
docker compose -f lab/01-container-wont-start/compose.yaml up -d
docker compose -f lab/01-container-wont-start/compose.yaml ps
docker compose -f lab/01-container-wont-start/compose.yaml logs
docker compose -f lab/01-container-wont-start/compose.yaml down
```

Stop a scenario with `docker compose ... down`. The lab never runs `docker system prune`.
