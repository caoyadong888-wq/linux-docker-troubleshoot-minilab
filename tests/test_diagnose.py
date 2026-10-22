"""Checker default is dry-run, reports both classes, and writes nothing."""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def _load_diagnose():
    path = ROOT / "check" / "diagnose.py"
    spec = importlib.util.spec_from_file_location("minilab_diagnose", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DIAG = _load_diagnose()


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "check/diagnose.sh", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_default_invocation_is_dry_run_and_exits_on_faults():
    proc = _run([])
    assert proc.returncode == 2
    assert proc.stderr == ""
    text = proc.stdout
    assert "mode=dry-run" in text
    assert "writes=none" in text
    assert "class=container-wont-start" in text
    assert "class=container-unhealthy" in text
    assert "class=port-connectivity" in text
    assert "broken.conf" in text
    assert "/healthz" in text
    assert "8080" in text
    assert "curl" in text and "wget" in text
    assert "probe=http://127.0.0.1:18082/" in text
    assert "faults=3" in text
    assert text.strip().endswith("result=FAULT")


def test_explicit_dry_run_matches_the_default():
    default = _run([])
    flagged = _run(["--dry-run"])
    assert default.returncode == flagged.returncode == 2
    assert default.stdout == flagged.stdout


def test_fixed_compose_files_are_clean():
    proc = _run(
        [
            "--dry-run",
            "--compose",
            "lab/01-container-wont-start/compose.fixed.yaml",
            "--compose",
            "lab/02-port-connectivity/compose.fixed.yaml",
        ]
    )
    assert proc.returncode == 0, proc.stderr
    assert "result=FAULT" not in proc.stdout
    assert "faults=0" in proc.stdout
    assert proc.stdout.strip().endswith("result=OK")
    assert "class=none" in proc.stdout


def test_dry_run_creates_no_package_files(tmp_path: Path):
    del tmp_path
    before = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts
    }
    proc = _run(["--dry-run"])
    after = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and ".pytest_cache" not in path.parts
    }
    assert proc.returncode == 2
    assert before == after


def test_dry_run_does_not_call_subprocess(monkeypatch: pytest.MonkeyPatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("subprocess was called")

    monkeypatch.setattr(DIAG.subprocess, "run", boom)
    assert DIAG.main([]) == 2


def test_source_has_no_write_or_shell_and_no_prune():
    source = (ROOT / "check" / "diagnose.py").read_text(encoding="utf-8")
    shell = (ROOT / "check" / "diagnose.sh").read_text(encoding="utf-8")
    assert "prune" not in source
    assert "prune" not in shell
    assert "sudo" not in source
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        assert name not in {"write_text", "write_bytes", "unlink", "mkdir", "rmtree", "system"}
        if name == "open":
            mode = None
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = str(node.args[1].value)
            for keyword in node.keywords:
                if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant):
                    mode = str(keyword.value.value)
            if mode is not None:
                assert "w" not in mode and "a" not in mode and "+" not in mode
        if name == "run":
            for keyword in node.keywords:
                if keyword.arg == "shell":
                    assert not isinstance(keyword.value, ast.Constant) or keyword.value.value is False


def test_live_and_dry_run_together_exit_nonzero():
    proc = _run(["--live", "--dry-run"])
    assert proc.returncode == 1
    assert "error=pass either" in proc.stderr


def test_live_without_docker_exits_nonzero(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(DIAG.shutil, "which", lambda _name: None)
    code = DIAG.main(["--live"])
    assert code == 1


def test_missing_compose_exits_nonzero():
    proc = _run(["--compose", "lab/missing-compose.yaml"])
    assert proc.returncode == 1
    assert "missing file" in proc.stderr


def test_structural_rules_on_temp_files(tmp_path: Path):
    port = tmp_path / "port.yaml"
    port.write_text(
        "\n".join(
            [
                "services:",
                "  web:",
                "    image: nginx:1.27-alpine",
                '    ports: ["127.0.0.1:18082:8080"]',
            ]
        ),
        encoding="utf-8",
    )
    proc = DIAG.main(["--dry-run", "--compose", str(port)])
    assert proc == 2
    health = tmp_path / "health.yaml"
    health.write_text(
        "\n".join(
            [
                "services:",
                "  web:",
                "    image: nginx:1.27-alpine",
                '    ports: ["127.0.0.1:18083:80"]',
                "    healthcheck:",
                '      test: ["CMD", "wget", "-q", "http://127.0.0.1/healthz"]',
            ]
        ),
        encoding="utf-8",
    )
    assert DIAG.main(["--dry-run", "--compose", str(health)]) == 2
    clean = tmp_path / "clean.yaml"
    clean.write_text(
        "\n".join(
            [
                "services:",
                "  web:",
                "    image: nginx:1.27-alpine",
                '    ports: ["127.0.0.1:18082:80"]',
            ]
        ),
        encoding="utf-8",
    )
    assert DIAG.main(["--dry-run", "--compose", str(clean)]) == 0
    public = tmp_path / "public.yaml"
    public.write_text(
        "\n".join(
            [
                "services:",
                "  web:",
                "    image: nginx:1.27-alpine",
                '    ports: ["18082:80"]',
            ]
        ),
        encoding="utf-8",
    )
    assert DIAG.main(["--live", "--compose", str(public)]) == 1
