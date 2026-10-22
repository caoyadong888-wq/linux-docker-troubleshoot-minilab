"""Required files, README sections, license, and changelog."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "README.md",
    "README.zh.md",
    "ACCEPTANCE.md",
    "LICENSE",
    "CHANGELOG.md",
    "requirements.txt",
    "lab/README.md",
    "lab/01-container-wont-start/compose.yaml",
    "lab/01-container-wont-start/compose.fixed.yaml",
    "lab/01-container-wont-start/EXPECTED.md",
    "lab/01-container-wont-start/FIX.md",
    "lab/02-port-connectivity/compose.yaml",
    "lab/02-port-connectivity/compose.fixed.yaml",
    "lab/02-port-connectivity/EXPECTED.md",
    "lab/02-port-connectivity/FIX.md",
    "check/diagnose.sh",
    "check/diagnose.py",
    "demo/demo.md",
    "demo/run-demo.sh",
    "demo/captured-output.txt",
    "tests/run_tests.sh",
    "tests/RESULTS.md",
)

EN_SECTIONS = ("## Purpose", "## Inputs", "## Steps", "## Acceptance", "## Boundaries", "## Requirements")
ZH_SECTIONS = ("## 目的", "## 输入", "## 步骤", "## 验收", "## 边界", "## 要求")


def test_required_files_exist():
    missing = [rel for rel in REQUIRED if not (ROOT / rel).is_file()]
    assert not missing, missing


def test_english_readme_sections_and_fault_ids():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in EN_SECTIONS:
        assert heading in text
    for token in (
        "container-wont-start",
        "container-unhealthy",
        "port-connectivity",
        "127.0.0.1",
        "example.com",
        "--dry-run",
        "curl",
        "wget",
        "docker system prune",
    ):
        assert token in text


def test_chinese_readme_sections_and_fault_ids():
    text = (ROOT / "README.zh.md").read_text(encoding="utf-8")
    for heading in ZH_SECTIONS:
        assert heading in text
    for token in (
        "container-wont-start",
        "unhealthy",
        "port-connectivity",
        "127.0.0.1",
        "example.com",
        "--dry-run",
        "curl",
        "wget",
        "docker system prune",
    ):
        assert token in text


def test_acceptance_is_a_checkbox_list():
    text = (ROOT / "ACCEPTANCE.md").read_text(encoding="utf-8")
    assert text.count("- [ ]") >= 8
    assert "container-wont-start" in text
    assert "container-unhealthy" in text
    assert "port-connectivity" in text
    assert "FAILS=0" in text


def test_license_and_changelog():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in license_text
    assert "Permission is hereby granted" in license_text
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## 1.0.0 - 2026-10-22" in changelog
    assert "container-wont-start" in changelog or "wont-start" in changelog
    assert "port" in changelog.lower()
