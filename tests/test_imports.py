"""Vérifie que tous les modules s'importent et que le lint est propre."""

import importlib
import os
import subprocess
import sys

import pytest

MODULES = [
    "LocalizationToolKit",
    "core",
    "core.colors",
    "core.i18n",
    "core.menu_helpers",
    "core.output_formatters",
    "core.paths",
    "tools",
    "tools.applicator",
    "tools.applicator.main",
    "tools.applicator.menu",
    "tools.extractor",
    "tools.extractor.config",
    "tools.extractor.engine",
    "tools.extractor.main",
    "tools.extractor.menu",
    "tools.extractor.models",
    "tools.extractor.output",
    "tools.extractor.report",
    "tools.extractor.utils",
    "tools.toolbox",
    "tools.toolbox.delete_temp_dir",
    "tools.toolbox.restore_backup",
    "tools.translator",
    "tools.translator.addlang",
    "tools.translator.autosync",
    "tools.translator.common",
    "tools.translator.compare",
    "tools.translator.compare_langs",
    "tools.translator.config_loader",
    "tools.translator.extract",
    "tools.translator.inject",
    "tools.translator.install",
    "tools.translator.main",
    "tools.translator.sync",
]


@pytest.mark.parametrize("module", MODULES)
def test_import_module(module):
    importlib.import_module(module)


def test_ruff_check_clean(toolkit_root):
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=toolkit_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    # Garde-fou : un ruff absent ne doit pas faire passer le test en silence
    assert "All checks passed" in result.stdout, result.stdout + result.stderr
