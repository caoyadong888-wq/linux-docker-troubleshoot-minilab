"""The captured stdout is a successful dry-run of broken then fixed labs."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_demo_script_matches_captured_stdout():
    proc = subprocess.run(
        ["bash", "demo/run-demo.sh"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == ""
    captured = (ROOT / "demo" / "captured-output.txt").read_text(encoding="utf-8")
    assert proc.stdout == captured
    assert "mode=dry-run" in captured
    assert "writes=none" in captured
    assert "class=container-wont-start" in captured
    assert "class=container-unhealthy" in captured
    assert "class=port-connectivity" in captured
    assert "faults=0" in captured
    assert "demo_result=OK" in captured
    assert captured.strip().endswith("demo_result=OK")


def test_demo_notes_name_the_commands():
    text = (ROOT / "demo" / "demo.md").read_text(encoding="utf-8")
    assert "bash check/diagnose.sh --dry-run" in text
    assert "bash demo/run-demo.sh" in text
    assert "captured-output.txt" in text
    assert "demo_result=OK" in text
