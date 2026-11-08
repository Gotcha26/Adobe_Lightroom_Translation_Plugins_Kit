"""CLI, menus et COMPARE : suites de la PR #33 (#37, sections CLI et Menus)."""

import importlib
import json
import os
import sys

import pytest


# =============================================================================
# Options --yes / --dry-run refusées quand la commande ne les prend pas en charge
# =============================================================================

@pytest.fixture
def launcher_capture(plugin_dir, isolated_config, monkeypatch):
    """Capture les arguments passés aux scripts au lieu de les lancer."""
    import LocalizationToolKit

    captured = []
    monkeypatch.setattr(LocalizationToolKit.ToolLauncher, "_run_script",
                        lambda self, script, args=None, cwd=None: captured.append(args) or True)
    monkeypatch.setattr(LocalizationToolKit.ToolLauncher, "find_latest_extraction",
                        lambda self: "EXTRACTION")
    monkeypatch.setattr(LocalizationToolKit.ConfigManager, "get",
                        lambda self, key, default=None: plugin_dir if key == "plugin_path" else default)
    return captured


def _toolkit_main(monkeypatch, *args):
    import LocalizationToolKit

    monkeypatch.setattr(sys, "argv", ["LocalizationToolKit.py", *args])
    with pytest.raises(SystemExit) as exc:
        LocalizationToolKit.main()
    return exc.value.code


@pytest.mark.parametrize(("command", "option"), [
    ("extract", "--dry-run"),
    ("autosync", "--dry-run"),
    ("translate", "--yes"),
    ("translate", "--dry-run"),
    ("restore", "--yes"),
    ("delete", "--dry-run"),
    ("config", "--yes"),
    ("7", "--dry-run"),
])
def test_launcher_refuses_unsupported_option(launcher_capture, monkeypatch, capsys, command, option):
    assert _toolkit_main(monkeypatch, command, option) == 2
    assert launcher_capture == []
    assert option in capsys.readouterr().out


@pytest.mark.parametrize(("command", "options"), [
    ("apply", ["--dry-run", "--yes"]),
    ("autosync", ["--yes"]),
    ("extract", ["--yes"]),
])
def test_launcher_accepts_supported_options(launcher_capture, monkeypatch, command, options):
    assert _toolkit_main(monkeypatch, command, *options) == 0
    assert len(launcher_capture) == 1


# =============================================================================
# clear_screen : seulement sur un terminal
# =============================================================================

def _clear_screen_callers():
    import LocalizationToolKit
    from core.cli import clear_screen as shared
    from tools.applicator.menu import ApplicatorMenu
    from tools.extractor.menu import InteractiveMenu
    from tools.translator.common import clear_screen as translator_clear

    return {
        "core": shared,
        "launcher": lambda: LocalizationToolKit.MainMenu.clear_screen(None),
        "applicator": lambda: ApplicatorMenu.clear_screen(None),
        "extractor": lambda: InteractiveMenu.clear_screen(None),
        "translator": translator_clear,
        "toolbox_delete": importlib.import_module("tools.toolbox.delete_temp_dir").clear_screen,
        "toolbox_restore": importlib.import_module("tools.toolbox.restore_backup").clear_screen,
    }


@pytest.mark.parametrize("name", ["core", "launcher", "applicator", "extractor", "translator",
                                  "toolbox_delete", "toolbox_restore"])
def test_clear_screen_silent_without_terminal(monkeypatch, name):
    calls = []
    monkeypatch.setattr(os, "system", lambda cmd: calls.append(cmd))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False, raising=False)
    _clear_screen_callers()[name]()
    assert calls == []


@pytest.mark.parametrize("name", ["core", "launcher", "applicator", "extractor", "translator"])
def test_clear_screen_runs_on_terminal(monkeypatch, name):
    calls = []
    monkeypatch.setattr(os, "system", lambda cmd: calls.append(cmd))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True, raising=False)
    _clear_screen_callers()[name]()
    assert len(calls) == 1


# =============================================================================
# input_extraction_dir : re-sélectionner le dossier courant le confirme
# =============================================================================

def _applicator_menu(plugin_dir, current):
    from tools.applicator.menu import ApplicatorMenu

    menu = ApplicatorMenu(plugin_dir)
    menu.extraction_dir = current
    return menu


def test_reselecting_current_extraction_dir_confirms_it(tmp_path, plugin_dir, monkeypatch, capsys):
    current = str(tmp_path / "extraction")
    os.makedirs(current)
    with open(os.path.join(current, "replacements.json"), "w", encoding="utf-8") as f:
        json.dump({}, f)
    menu = _applicator_menu(plugin_dir, current)
    monkeypatch.setattr("tools.applicator.menu.choose_tool_output_dir", lambda *a, **k: (current, False))

    assert menu.input_extraction_dir() is True
    assert menu.extraction_dir == current
    assert "confirmé" in capsys.readouterr().out


def test_reselecting_current_extraction_dir_still_validates_it(tmp_path, plugin_dir, monkeypatch):
    """Un dossier courant sans replacements.json n'est plus accepté sans question."""
    current = str(tmp_path / "extraction")
    os.makedirs(current)
    menu = _applicator_menu(plugin_dir, current)
    monkeypatch.setattr("tools.applicator.menu.choose_tool_output_dir", lambda *a, **k: (current, False))
    monkeypatch.setattr("builtins.input", lambda *a: "n")

    assert menu.input_extraction_dir() is False


def test_cancelling_extraction_dir_selection_keeps_current_silently(tmp_path, plugin_dir, monkeypatch, capsys):
    """Annuler (vrai helper, ENTRÉE) ne confirme pas et ne relance aucun contrôle ni question."""
    current = str(tmp_path / "extraction")
    os.makedirs(current)  # sans replacements.json : une validation poserait une question
    menu = _applicator_menu(plugin_dir, current)
    asked = []
    monkeypatch.setattr("builtins.input", lambda *a: asked.append(a) or "")

    assert menu.input_extraction_dir() is True
    assert menu.extraction_dir == current
    assert len(asked) == 1  # seulement la saisie du helper
    out = capsys.readouterr().out
    assert "confirmé" not in out
    assert "Fichiers manquants" not in out


def test_choose_tool_output_dir_distinguishes_cancel_from_reselect(tmp_path, monkeypatch):
    from core.menu_helpers import choose_tool_output_dir

    plugin = str(tmp_path / "p.lrplugin")
    os.makedirs(plugin)
    current = str(tmp_path / "extraction")
    os.makedirs(current)

    monkeypatch.setattr("builtins.input", lambda *a: "")
    assert choose_tool_output_dir(plugin, "Extractor", current) == (current, True)

    monkeypatch.setattr("builtins.input", lambda *a: current)
    assert choose_tool_output_dir(plugin, "Extractor", current) == (current, False)

    monkeypatch.setattr("builtins.input", lambda *a: str(tmp_path / "absent"))
    assert choose_tool_output_dir(plugin, "Extractor", current) == (None, False)


# =============================================================================
# menu_extract : l'annulation est signalée
# =============================================================================

def test_menu_extract_cancel_is_reported(plugin_dir, monkeypatch, capsys):
    from tools.translator import extract

    monkeypatch.setattr("tools.translator.common.clear_screen", lambda: None)
    monkeypatch.setattr("core.menu_helpers.select_tool_output_dir", lambda *a, **k: "")
    answers = []
    monkeypatch.setattr("builtins.input", lambda *a: answers.append(a) or "")

    assert extract.menu_extract(plugin_dir) is None
    out = capsys.readouterr().out
    assert "annulée" in out
    assert len(answers) == 1  # pause avant le retour au menu


# =============================================================================
# COMPARE : langue de référence dans le CHANGELOG
# =============================================================================

def test_compare_changelog_uses_reference_lang(isolated_config, plugin_dir, tmp_path):
    from tools.translator.compare import run_compare

    with open(os.path.join(isolated_config, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"lang": "fr", "prefix": "$$$/Test", "temp_dir": "__i18n_tmp__"}, f)

    old = tmp_path / "old.txt"
    new = tmp_path / "new.txt"
    old.write_text('"$$$/Test/A=Bonjour"\n"$$$/Test/B=Salut"\n', encoding="utf-8")
    new.write_text('"$$$/Test/A=Bonsoir"\n"$$$/Test/C=Merci"\n', encoding="utf-8")
    out = str(tmp_path / "out")

    run_compare(str(old), str(new), out)

    with open(os.path.join(out, "CHANGELOG.txt"), encoding="utf-8") as f:
        changelog = f.read()
    assert "traductions fr" in changelog
    assert "fr: Merci" in changelog
    assert "EN" not in changelog
