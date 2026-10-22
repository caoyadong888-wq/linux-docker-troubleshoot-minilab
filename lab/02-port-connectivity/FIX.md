# FIX · port connectivity

Change the published container port from `8080` to `80`.

Broken:

```yaml
ports:
  - "127.0.0.1:18082:8080"
```

Fixed (see `compose.fixed.yaml`):

```yaml
ports:
  - "127.0.0.1:18082:80"
```

Keep the host address on `127.0.0.1`. The host port can stay `18082`.

## Check again

```bash
bash check/diagnose.sh --dry-run --compose lab/02-port-connectivity/compose.fixed.yaml
```

Expect `faults=0`, `result=OK`, and exit `0`.

## Optional live start

```bash
docker compose -f lab/02-port-connectivity/compose.yaml up -d
curl -fsS --max-time 3 http://127.0.0.1:18082/ ; echo "broken_curl_exit=$?"
docker compose -f lab/02-port-connectivity/compose.yaml down

docker compose -f lab/02-port-connectivity/compose.fixed.yaml up -d
curl -fsS --max-time 3 http://127.0.0.1:18082/ ; echo "fixed_curl_exit=$?"
docker compose -f lab/02-port-connectivity/compose.fixed.yaml down
```

The broken curl exits non-zero. The fixed curl exits `0` when the image is present and port `18082` is free. `down` stops this project only.
