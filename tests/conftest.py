"""Write tests/RESULTS.md when the pytest session finishes."""

from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True

RESULTS = Path(__file__).resolve().parent / "RESULTS.md"


def pytest_sessionfinish(session, exitstatus):
    del exitstatus
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return
    stats = reporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    errors = len(stats.get("error", []))
    fails = failed + errors
    RESULTS.write_text(
        "\n".join(
            [
                "# Test results",
                "",
                "command: python3 -m pytest -q -p no:cacheprovider tests",
                f"passed: {passed}",
                f"failed: {failed}",
                f"skipped: {skipped}",
                f"errors: {errors}",
                "",
                f"FAILS={fails}",
                "",
            ]
        ),
        encoding="utf-8",
    )
