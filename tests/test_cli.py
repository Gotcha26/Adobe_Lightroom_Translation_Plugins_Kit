"""Mode CLI cohérent (#26).

- Un seul argparse par outil (--default-plugin, --yes) ; mode interactif
  uniquement sans argument « action ».
- Sous-commandes install / addlang / autosync du Translator.
- Lanceur : apply --dry-run optionnel, --yes propagé seulement s'il est donné,
  numérotation fixe du menu (6 = AUTO-SYNC, 7 = Configuration).
- Applicator : aucun prompt en script, code retour 1 si des fichiers manquent.
"""

import os
import subprocess
import sys

import pytest

from core.i18n import _


def _run(args, cwd, timeout=60):
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        stdin=subprocess.DEVNULL,
        timeout=timeout,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def _lua_contents(plugin_dir):
    contents = {}
    for root, dirs, files in os.walk(plugin_dir):
        dirs[:] = [d for d in dirs if not d.startswith("__")]
        for name in files:
            if name.endswith(".lua"):
                path = os.path.join(root, name)
                with open(path, encoding="utf-8") as f:
                    contents[os.path.relpath(path, plugin_dir)] = f.read()
    return contents


@pytest.fixture
def extracted_plugin(plugin_dir, toolkit_root):
    """Plugin de test sur lequel l'Extractor a déjà tourné (sous-processus)."""
    result = _run(["-m", "tools.extractor.main", "--plugin-path", plugin_dir, "--prefix", "$$$/Test"],
                  toolkit_root)
    assert result.returncode == 0, result.stdout + result.stderr
    return plugin_dir


# =============================================================================
# Sous-processus
# =============================================================================

@pytest.mark.parametrize("subcommand", ["install", "addlang", "autosync"])
def test_translator_subcommand_help(subcommand, toolkit_root):
    result = _run(["-m", "tools.translator.main", subcommand, "--help"], toolkit_root)
    assert result.returncode == 0, result.stdout + result.stderr


def test_applicator_cli_dry_run_yes_does_not_block(extracted_plugin, toolkit_root):
    before = _lua_contents(extracted_plugin)
    result = _run(["-m", "tools.applicator.main", "--plugin-path", extracted_plugin, "--dry-run", "--yes"],
                  toolkit_root)
    assert result.returncode == 0, result.stdout + result.stderr
    assert _lua_contents(extracted_plugin) == before


@pytest.mark.parametrize("extra_args", [["--yes"], []])
def test_applicator_cli_real_run_without_tty_does_not_prompt(extracted_plugin, toolkit_root, extra_args):
    before = _lua_contents(extracted_plugin)
    result = _run(["-m", "tools.applicator.main", "--plugin-path", extracted_plugin, *extra_args], toolkit_root)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EOFError" not in result.stderr
    assert _lua_contents(extracted_plugin) != before


# =============================================================================
# Applicator : code retour
# =============================================================================

def test_process_plugin_directory_fails_when_file_missing(plugin_dir, isolated_config):
    from tools.applicator.main import process_plugin_directory
    from tools.extractor.main import run_extraction

    run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, True, silent=True)
    os.remove(os.path.join(plugin_dir, "PWExport.lua"))

    success, report = process_plugin_directory(plugin_dir, dry_run=True, silent=True)

    assert report.errors
    assert success is False


# =============================================================================
# Points d'entrée en processus : --default-plugin via argparse
# =============================================================================

def test_extractor_default_plugin_opens_menu(monkeypatch, plugin_dir):
    from tools.extractor import main as extractor_main

    calls = []
    monkeypatch.setattr(extractor_main, "show_interactive_menu", lambda path: calls.append(path))
    monkeypatch.setattr(sys, "argv", ["main.py", "--default-plugin", plugin_dir])

    with pytest.raises(SystemExit):
        extractor_main.main()

    assert calls == [plugin_dir]


def test_applicator_default_plugin_with_dry_run_opens_menu(monkeypatch, plugin_dir):
    from tools.applicator import main as applicator_main

    calls = []
    monkeypatch.setattr(applicator_main, "show_interactive_menu", lambda path: calls.append(path))
    monkeypatch.setattr(sys, "argv", ["main.py", "--default-plugin", plugin_dir, "--dry-run"])

    with pytest.raises(SystemExit):
        applicator_main.main()

    assert calls == [plugin_dir]


def test_translator_default_plugin_opens_menu(monkeypatch, plugin_dir):
    from tools.translator import main as translator_main

    calls = []
    monkeypatch.setattr(translator_main, "main_menu", lambda path="": calls.append(path))
    monkeypatch.setattr(sys, "argv", ["main.py", "--default-plugin", plugin_dir])

    translator_main.main()

    assert calls == [plugin_dir]


def test_translator_install_subcommand(monkeypatch, plugin_dir):
    from tools.translator import main as translator_main

    calls = []
    monkeypatch.setattr(translator_main, "run_install",
                        lambda *a, **k: calls.append((a, k)) or True)
    monkeypatch.setattr(sys, "argv", ["main.py", "install", "--plugin-path", plugin_dir,
                                      "--source", "src", "--dry-run"])

    with pytest.raises(SystemExit) as exc:
        translator_main.main()

    assert exc.value.code == 0
    assert calls == [((plugin_dir,), {"source_dir": "src", "dry_run": True})]


def test_translator_addlang_subcommand(monkeypatch, plugin_dir):
    from tools.translator import main as translator_main

    calls = []
    monkeypatch.setattr(translator_main, "run_addlang_cli",
                        lambda *a, **k: calls.append((a, k)) or False)
    monkeypatch.setattr(sys, "argv", ["main.py", "addlang", "--plugin-path", plugin_dir,
                                      "--lang", "de", "--mode", "create", "--force"])

    with pytest.raises(SystemExit) as exc:
        translator_main.main()

    assert exc.value.code == 1
    assert calls == [((plugin_dir, "de"), {"mode": "create", "force": True})]


# =============================================================================
# Lanceur LocalizationToolKit
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


@pytest.mark.parametrize(("extra_args", "expected_flags"), [
    (["--dry-run"], ["--dry-run"]),
    (["--yes"], ["--yes"]),
    (["--dry-run", "--yes"], ["--dry-run", "--yes"]),
])
def test_toolkit_apply_dry_run_only_when_requested(launcher_capture, plugin_dir, monkeypatch,
                                                   extra_args, expected_flags):
    assert _toolkit_main(monkeypatch, "apply", *extra_args) == 0
    assert launcher_capture == [["--plugin-path", plugin_dir, "--extraction-dir", "EXTRACTION", *expected_flags]]


@pytest.mark.parametrize(("extra_args", "expected"), [([], []), (["--yes"], ["--yes"])])
def test_toolkit_autosync_forwards_yes_only_when_given(launcher_capture, plugin_dir, monkeypatch,
                                                       extra_args, expected):
    assert _toolkit_main(monkeypatch, "autosync", *extra_args) == 0
    assert launcher_capture == [["autosync", "--plugin-path", plugin_dir, *expected]]


def test_toolkit_translation_manager_cli_launches_autosync(launcher_capture, plugin_dir, toolkit_root):
    import LocalizationToolKit

    launcher = LocalizationToolKit.ToolLauncher(toolkit_root, LocalizationToolKit.ConfigManager(toolkit_root))
    assert launcher.run_translation_manager(interactive=False)
    assert launcher_capture == [["autosync", "--plugin-path", plugin_dir]]


def test_toolkit_cli_7_does_not_launch_autosync(launcher_capture, monkeypatch):
    import LocalizationToolKit

    calls = []
    monkeypatch.setattr(LocalizationToolKit.ToolLauncher, "run_autosync",
                        lambda self, **k: calls.append(k) or True)

    assert _toolkit_main(monkeypatch, "7") == 0
    assert calls == []
    assert launcher_capture == []


def test_toolkit_cli_rejects_unknown_option(launcher_capture, monkeypatch):
    assert _toolkit_main(monkeypatch, "apply", "--bogus") != 0
    assert launcher_capture == []


# =============================================================================
# Menu principal : numérotation fixe
# =============================================================================

@pytest.fixture
def menu_factory(plugin_dir, isolated_config, monkeypatch):
    """Construit un MainMenu isolé dont les actions sont enregistrées."""
    import LocalizationToolKit

    def build(with_translations: bool, answers):
        if not with_translations:
            for name in os.listdir(plugin_dir):
                if name.startswith("TranslatedStrings_"):
                    os.remove(os.path.join(plugin_dir, name))
        menu = LocalizationToolKit.MainMenu()
        menu.config.config["plugin_path"] = plugin_dir
        calls = []
        monkeypatch.setattr(menu, "clear_screen", lambda: None)
        monkeypatch.setattr(menu, "print_header", lambda: None)
        monkeypatch.setattr(menu, "configure_paths", lambda: calls.append("config"))
        monkeypatch.setattr(menu.launcher, "run_autosync", lambda **k: calls.append("autosync") or True)
        feed = iter(answers)
        monkeypatch.setattr("builtins.input", lambda *_a: next(feed, "0"))
        return menu, calls

    return build


@pytest.mark.parametrize("with_translations", [True, False])
def test_menu_7_is_always_configuration(menu_factory, with_translations):
    menu, calls = menu_factory(with_translations, ["7"])
    menu.run()
    assert calls == ["config"]


def test_menu_6_is_autosync_when_translations_exist(menu_factory):
    menu, calls = menu_factory(True, ["6", ""])
    menu.run()
    assert calls == ["autosync"]


def test_menu_6_without_translations_explains_and_returns(menu_factory, capsys):
    menu, calls = menu_factory(False, ["6", ""])
    menu.run()
    assert calls == []
    out = capsys.readouterr().out
    assert _("(aucun TranslatedStrings)") in out
