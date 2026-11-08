"""Détection de la langue système (#23)."""

import locale
import subprocess
import sys

import pytest

from core import i18n

ENV_VARS = ("TOOLKIT_LANG", "LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE")


@pytest.fixture
def clean_env(monkeypatch):
    for var in ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(locale, "getlocale", lambda *a, **k: (None, None))
    return monkeypatch


def test_toolkit_lang_unsupported_falls_back_to_en(clean_env):
    clean_env.setenv("TOOLKIT_LANG", "xx")
    assert i18n._detect_system_language() == "en"


def test_lang_variable_fr(clean_env):
    clean_env.setenv("LANG", "fr_FR.UTF-8")
    assert i18n._detect_system_language() == "fr"


def test_lc_all_has_priority_over_lang(clean_env):
    clean_env.setenv("LC_ALL", "en_US.UTF-8")
    clean_env.setenv("LANG", "fr_FR.UTF-8")
    assert i18n._detect_system_language() == "en"


def test_language_variable_list(clean_env):
    clean_env.setenv("LANGUAGE", "fr:en")
    assert i18n._detect_system_language() == "fr"


def test_toolkit_lang_has_priority_over_lang(clean_env):
    clean_env.setenv("TOOLKIT_LANG", "en")
    clean_env.setenv("LANG", "fr_FR.UTF-8")
    assert i18n._detect_system_language() == "en"


def test_windows_getlocale_french(clean_env):
    clean_env.setattr(locale, "getlocale", lambda *a, **k: ("French_France", "1252"))
    assert i18n._detect_system_language() == "fr"


def test_windows_getlocale_english_case_insensitive(clean_env):
    clean_env.setattr(locale, "getlocale", lambda *a, **k: ("english_united states", "1252"))
    assert i18n._detect_system_language() == "en"


def test_nothing_detected_falls_back(clean_env):
    assert i18n._detect_system_language() == i18n.FALLBACK_LANGUAGE


def test_getdefaultlocale_never_called(clean_env):
    calls = []
    clean_env.setattr(locale, "getdefaultlocale", lambda *a, **k: calls.append(1) or (None, None), raising=False)
    i18n._detect_system_language()
    i18n.debug_language_detection()
    assert calls == []


def test_import_raises_no_deprecation_warning(toolkit_root):
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", "import core.i18n"],
        cwd=toolkit_root, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
