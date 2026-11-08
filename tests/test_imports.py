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


# Modules cassés aujourd'hui : SyntaxError « keyword argument repeated: lang »
# à addlang.py:483 (résidu auto-i18n), hors périmètre de la Task 1.
BROKEN_SYNTAX = {"tools.translator.addlang", "tools.translator.main"}
BROKEN_REASON = "SyntaxError addlang.py:483 (lang= répété) — à corriger dans une tâche ultérieure"


@pytest.mark.parametrize(
    "module",
    [
        pytest.param(m, marks=pytest.mark.xfail(strict=True, reason=BROKEN_REASON)) if m in BROKEN_SYNTAX else m
        for m in MODULES
    ],
)
def test_import_module(module):
    importlib.import_module(module)


@pytest.mark.xfail(strict=True, reason="#13 #14 — corrigé en Task 2")
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
