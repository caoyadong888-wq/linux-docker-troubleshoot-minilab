# EXPECTED · port connectivity

Project name: `minilab-port-connectivity`.

- Image `nginx:1.27-alpine` listens on container port 80.
- The port mapping is `127.0.0.1:18082:8080`.
- The container can be `Up` while the published port still fails.
- `curl -fsS --max-time 3 http://127.0.0.1:18082/` fails.
- `wget -q -O /dev/null http://127.0.0.1:18082/` fails.
- The failure is a connection refusal on the mapped container port, because nothing listens on 8080 inside the container.
- A probe from inside the container to `http://127.0.0.1/` on port 80 can still succeed. That shows the process is fine and the mapping is wrong.
- Class id: `port-connectivity`.
- Checker: `bash check/diagnose.sh --dry-run` includes this scenario as `result=FAULT` and exits non-zero. The probe line is `http://127.0.0.1:18082/`.
