#!/usr/bin/env python3
"""Read-only minilab diagnose. Default mode is dry-run.

Dry-run reads Compose YAML and writes nothing. Live mode is opt-in and
only runs read-only `docker compose ps` plus curl to 127.0.0.1.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment has PyYAML
    print("error=PyYAML is required (python3 -m pip install pyyaml)", file=sys.stderr)
    raise SystemExit(1)

VERSION = "1.0.0"
MAX_BYTES = 1_000_000
NGINX_LISTEN = "80"


def package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def scenario_name(path: Path, root: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        rel = path
    if len(rel.parts) >= 2 and rel.parts[0] == "lab":
        return rel.parts[1]
    return path.stem


def default_compose_files(root: Path) -> list[Path]:
    lab = root / "lab"
    return sorted(path for path in lab.glob("*/compose.yaml") if path.is_file())


def load_compose(path: Path) -> dict:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"file too large: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"compose root must be a mapping: {path}")
    return data


def normalize_command(command) -> list[str]:
    if command is None:
        return []
    if isinstance(command, str):
        return command.split()
    if isinstance(command, list):
        return [str(item) for item in command]
    raise ValueError("command must be a string or a list")


def config_path_from_command(args: list[str]) -> str | None:
    if "-c" not in args:
        return None
    index = args.index("-c")
    if index + 1 >= len(args):
        return None
    return args[index + 1]


def volume_container_paths(service: dict) -> list[str]:
    found: list[str] = []
    for item in service.get("volumes") or []:
        if isinstance(item, str):
            parts = item.split(":")
            if len(parts) >= 2:
                found.append(parts[1])
            continue
        if isinstance(item, dict):
            target = item.get("target")
            if target:
                found.append(str(target))
    return found


def path_is_mounted(config_path: str, mounts: list[str]) -> bool:
    for mount in mounts:
        if config_path == mount:
            return True
        prefix = mount.rstrip("/")
        if prefix and config_path.startswith(prefix + "/"):
            return True
    return False


def health_text(test) -> str:
    if test is None:
        return ""
    if isinstance(test, str):
        return test
    if isinstance(test, list):
        parts = [str(item) for item in test]
        if parts and parts[0] in {"CMD", "CMD-SHELL", "NONE"}:
            parts = parts[1:]
        return " ".join(parts)
    raise ValueError("healthcheck test must be a string or a list")


def first_url(text: str) -> str:
    for token in text.split():
        if token.startswith("http://") or token.startswith("https://"):
            return token
    return "-"


def listen_port(service: dict) -> str | None:
    image = str(service.get("image") or "")
    if image.startswith("nginx:"):
        return NGINX_LISTEN
    labels = service.get("labels") or {}
    if isinstance(labels, dict) and "com.example.minilab.listen-port" in labels:
        return str(labels["com.example.minilab.listen-port"])
    return None


def parse_port(entry) -> tuple[str, str, str]:
    if isinstance(entry, dict):
        host_ip = str(entry.get("host_ip") or "")
        published = entry.get("published")
        target = entry.get("target")
        if published is None or target is None:
            raise ValueError("port mapping needs published and target")
        return host_ip, str(published), str(target)
    text = str(entry).strip()
    parts = text.split(":")
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return "", parts[0], parts[1]
    raise ValueError(f"unsupported port mapping: {text}")


def finding(
    scenario: str,
    service: str,
    fault_class: str,
    result: str,
    probe: str,
    expected: str,
    detail: str,
) -> dict[str, str]:
    return {
        "scenario": scenario,
        "service": service,
        "class": fault_class,
        "result": result,
        "probe": probe,
        "expected": expected,
        "detail": detail,
    }


def analyze_service(scenario: str, name: str, service: dict) -> list[dict[str, str]]:
    if not isinstance(service, dict):
        raise ValueError(f"service {name} must be a mapping")
    rows: list[dict[str, str]] = []
    command = normalize_command(service.get("command"))
    config_path = config_path_from_command(command)
    if config_path and not path_is_mounted(config_path, volume_container_paths(service)):
        rows.append(
            finding(
                scenario,
                name,
                "container-wont-start",
                "FAULT",
                "-",
                "ps shows Exited or Restarting; the service does not stay up",
                (
                    f"command -c {config_path} has no matching volume; "
                    "the process exits and Compose does not keep it up"
                ),
            )
        )
    probe_text = health_text((service.get("healthcheck") or {}).get("test"))
    if "healthz" in probe_text:
        rows.append(
            finding(
                scenario,
                name,
                "container-unhealthy",
                "FAULT",
                first_url(probe_text),
                "ps shows Up (unhealthy) after the healthcheck retries",
                (
                    "healthcheck wget target contains /healthz; "
                    "the stock nginx image does not serve that path, "
                    "so the container becomes unhealthy"
                ),
            )
        )
    listen = listen_port(service)
    for entry in service.get("ports") or []:
        host_ip, host_port, container_port = parse_port(entry)
        if host_ip != "127.0.0.1":
            shown = host_ip or "0.0.0.0"
            rows.append(
                finding(
                    scenario,
                    name,
                    "non-loopback-bind",
                    "FAULT",
                    "-",
                    "published ports in this lab bind 127.0.0.1 only",
                    f"published host address is {shown}",
                )
            )
        if listen and container_port != listen:
            probe = f"http://127.0.0.1:{host_port}/" if host_ip == "127.0.0.1" else "-"
            rows.append(
                finding(
                    scenario,
                    name,
                    "port-connectivity",
                    "FAULT",
                    probe,
                    "the container can be running while curl and wget to the published port fail",
                    (
                        f"published container port {container_port} does not match "
                        f"listen port {listen}; curl and wget {probe} fail"
                    ),
                )
            )
    if not rows:
        rows.append(
            finding(
                scenario,
                name,
                "none",
                "OK",
                "-",
                "service stays up on the published loopback port",
                "no container, health, or port fault",
            )
        )
    return rows


def analyze_compose(data: dict, scenario: str) -> list[dict[str, str]]:
    services = data.get("services")
    if not isinstance(services, dict) or not services:
        raise ValueError("compose file needs a services mapping")
    rows: list[dict[str, str]] = []
    for name, service in services.items():
        rows.extend(analyze_service(scenario, str(name), service))
    networks = data.get("networks") or {}
    if isinstance(networks, dict):
        for net_name, spec in networks.items():
            if isinstance(spec, dict) and spec.get("external"):
                rows.append(
                    finding(
                        scenario,
                        str(net_name),
                        "external-network",
                        "FAULT",
                        "-",
                        "lab networks are created by this compose file",
                        "network is marked external",
                    )
                )
    return rows


def format_report(mode: str, rows: list[dict[str, str]]) -> str:
    faults = sum(1 for row in rows if row["result"] == "FAULT")
    lines = [
        f"minilab-diagnose version={VERSION}",
        f"mode={mode}",
        "writes=none",
    ]
    for row in rows:
        lines.append(
            "scenario={scenario} service={service} class={klass} result={result} "
            "probe={probe} expected={expected} detail={detail}".format(
                scenario=row["scenario"],
                service=row["service"],
                klass=row["class"],
                result=row["result"],
                probe=row["probe"],
                expected=row["expected"],
                detail=row["detail"],
            )
        )
    lines.append(f"faults={faults}")
    lines.append("result=FAULT" if faults else "result=OK")
    return "\n".join(lines) + "\n"


def loopback_http(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme == "http" and parsed.hostname == "127.0.0.1"


def run_live(paths: list[Path], rows: list[dict[str, str]]) -> int:
    if any(row["class"] == "non-loopback-bind" for row in rows):
        print("refuse=non-loopback")
        print("result=ERROR")
        return 1
    for row in rows:
        if row["probe"] != "-" and not loopback_http(row["probe"]):
            print("refuse=probe")
            print("result=ERROR")
            return 1
    if shutil.which("docker") is None:
        print("live_docker=unavailable")
        print("result=ERROR")
        return 1
    for path in paths:
        proc = subprocess.run(
            ["docker", "compose", "-f", str(path), "ps"],
            check=False,
            capture_output=True,
            text=True,
        )
        print(f"live_ps_exit={proc.returncode} file={path.name}")
    curl_bin = shutil.which("curl")
    if curl_bin:
        seen: set[str] = set()
        for row in rows:
            probe = row["probe"]
            if row["class"] != "port-connectivity" or probe in seen:
                continue
            if not loopback_http(probe):
                print("refuse=probe")
                print("result=ERROR")
                return 1
            seen.add(probe)
            proc = subprocess.run(
                [curl_bin, "-fsS", "--max-time", "3", "--output", "/dev/null", probe],
                check=False,
                capture_output=True,
                text=True,
            )
            print(f"live_curl_exit={proc.returncode} probe={probe}")
    faults = sum(1 for row in rows if row["result"] == "FAULT")
    print("result=FAULT" if faults else "result=OK")
    return 2 if faults else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diagnose",
        description="Read-only diagnose for the Linux/Docker minilab. Default is --dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Static check only. This is the default. Writes nothing.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Opt-in read-only docker compose ps and loopback curl. Writes nothing.",
    )
    parser.add_argument(
        "--compose",
        action="append",
        default=[],
        help="Compose file to read. Repeat for more than one. Default: lab/*/compose.yaml.",
    )
    return parser


def _main(argv: list[str] | None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code in (0, None):
            return 0
        return int(code)
    if args.live and args.dry_run:
        print("error=pass either --dry-run or --live", file=sys.stderr)
        return 1
    mode = "live" if args.live else "dry-run"
    root = package_root()
    if args.compose:
        paths = [Path(item) for item in args.compose]
    else:
        paths = default_compose_files(root)
    if not paths:
        print("error=no compose files", file=sys.stderr)
        return 1
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file():
            print(f"error=missing file {path}", file=sys.stderr)
            return 1
        data = load_compose(path)
        rows.extend(analyze_compose(data, scenario_name(path, root)))
    sys.stdout.write(format_report(mode, rows))
    if mode == "dry-run":
        faults = sum(1 for row in rows if row["result"] == "FAULT")
        return 2 if faults else 0
    return run_live(paths, rows)


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"error={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
