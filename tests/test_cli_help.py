"""Les trois CLI répondent à --help avec le code retour 0."""

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "tools.extractor.main",
        "tools.applicator.main",
        "tools.translator.main",
    ],
)
def test_cli_help(module, toolkit_root):
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        cwd=toolkit_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
