"""Broken labs show the two fault classes. Fixed labs remove them."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str) -> dict:
    data = yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_wont_start_lab_has_exit_and_unhealthy_services():
    data = _load("lab/01-container-wont-start/compose.yaml")
    assert data["name"] == "minilab-wont-start"
    services = data["services"]
    assert set(services) == {"web-exits", "web-unhealthy"}
    exits = services["web-exits"]
    assert exits["command"][2] == "/etc/nginx/broken.conf"
    assert "volumes" not in exits
    assert exits["ports"] == ["127.0.0.1:18081:80"]
    assert exits["hostname"].endswith(".example.com")
    unhealthy = services["web-unhealthy"]
    joined = " ".join(unhealthy["healthcheck"]["test"])
    assert "/healthz" in joined
    assert "wget" in joined
    assert unhealthy["ports"] == ["127.0.0.1:18083:80"]
    assert unhealthy["image"].startswith("nginx:")
    assert data["networks"]["labnet"]["driver"] == "bridge"
    assert "external" not in data["networks"]["labnet"]


def test_port_lab_publishes_the_wrong_container_port():
    data = _load("lab/02-port-connectivity/compose.yaml")
    web = data["services"]["web"]
    assert web["ports"] == ["127.0.0.1:18082:8080"]
    assert web["labels"]["com.example.minilab.listen-port"] == "80"
    assert web["labels"]["com.example.minilab.probe-url"] == "http://127.0.0.1:18082/"
    assert web["hostname"] == "web.lab.example.com"
    assert web["image"] == "nginx:1.27-alpine"
    assert "command" not in web


def test_fixed_labs_clear_the_intentional_faults():
    first = (ROOT / "lab/01-container-wont-start/compose.fixed.yaml").read_text(encoding="utf-8")
    second = (ROOT / "lab/02-port-connectivity/compose.fixed.yaml").read_text(encoding="utf-8")
    assert "broken.conf" not in first
    assert "healthz" not in first
    assert "8080" not in second
    data = _load("lab/01-container-wont-start/compose.fixed.yaml")
    for service in data["services"].values():
        assert "command" not in service
        assert "http://127.0.0.1/" in " ".join(service["healthcheck"]["test"])
    port = _load("lab/02-port-connectivity/compose.fixed.yaml")
    assert port["services"]["web"]["ports"] == ["127.0.0.1:18082:80"]


def test_compose_files_stay_unprivileged_and_on_loopback():
    files = list((ROOT / "lab").glob("*/compose*.yaml"))
    assert len(files) == 4
    for path in files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for service in data["services"].values():
            assert service.get("privileged") is not True
            assert service.get("network_mode") != "host"
            assert "docker.sock" not in str(service.get("volumes", ""))
            for entry in service.get("ports") or []:
                assert str(entry).startswith("127.0.0.1:")
            image = str(service["image"])
            assert image.startswith("nginx:")
            assert "registry." not in image
        for spec in (data.get("networks") or {}).values():
            assert not (isinstance(spec, dict) and spec.get("external"))
