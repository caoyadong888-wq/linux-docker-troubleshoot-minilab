"""No public IPs, real mailboxes, or credential material in this package."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b")
DOC_NETS = (
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
)
SKIP_SUFFIXES = {".png", ".pyc", ".zip", ".ttf", ".ttc", ".otf", ".woff"}
SECRET_RES = [
    re.compile("-----BEGIN " + r"(?:[A-Z0-9]+ )?" + "PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
    re.compile(r"(?i)\b(api[_-]?key|password|secret|token)\b\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
]


def _ip_allowed(text: str) -> bool:
    try:
        addr = ipaddress.ip_address(text)
    except ValueError:
        return True
    if any(addr in net for net in DOC_NETS):
        return True
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_unspecified
        or addr.is_link_local
        or addr.is_reserved
    )


def _email_allowed(address: str) -> bool:
    address = address.lower().rstrip(".")
    # Public contact email.
    if address == "caoyadong888@gmail.com":
        return True
    domain = address.rsplit("@", 1)[-1]
    if domain == "localhost":
        return True
    for base in ("example.com", "example.org", "example.net"):
        if domain == base or domain.endswith("." + base):
            return True
    return False


def _forbidden_ops_hosts() -> list[str]:
    octets = (
        ("3", "1", "79", "63"),
        ("52", "76", "87", "179"),
    )
    return [".".join(parts) for parts in octets]


def test_no_public_ips_real_emails_or_secrets():
    scanned = 0
    blob: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        blob.append(text)
        scanned += 1
        for match in IP_RE.findall(text):
            assert _ip_allowed(match), f"{path}: {match}"
        for domain in EMAIL_RE.findall(text):
            assert _email_allowed(domain), f"{path}: @{domain}"
        for pattern in SECRET_RES:
            found = pattern.search(text)
            assert found is None, f"{path}: {found.group(0) if found else pattern.pattern}"
    assert scanned > 10
    joined = "\n".join(blob)
    for host in _forbidden_ops_hosts():
        assert host not in joined


def test_lab_hostnames_use_example_com():
    found = 0
    for path in (ROOT / "lab").rglob("*.yaml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "hostname:" not in line:
                continue
            value = line.split("hostname:", 1)[1].strip().strip('"').strip("'")
            assert value.endswith(".example.com"), f"{path}: {value}"
            found += 1
    assert found >= 3
