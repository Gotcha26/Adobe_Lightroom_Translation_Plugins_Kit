"""Robustesse : chemins, dépôt git, encodage, couleurs, terminal (#32)."""

import os
import subprocess
import sys

import pytest

from core import paths


# =============================================================================
# CHEMINS
# =============================================================================

def test_display_relative_inside_plugin(tmp_path):
    plugin = tmp_path / "plugin.lrplugin"
    target = plugin / "__i18n_tmp__" / "1_Extractor" / "20260101_120000"
    assert paths.display_relative(str(target), str(plugin)) == "<plugin>/__i18n_tmp__/1_Extractor/20260101_120000"
    assert paths.display_relative(str(plugin), str(plugin)) == "<plugin>"


def test_display_relative_sibling_with_same_prefix_is_unchanged(tmp_path):
    plugin = tmp_path / "plugin.lrplugin"
    sibling = str(tmp_path / "plugin.lrplugin-old" / "x.lua")
    assert paths.display_relative(sibling, str(plugin)) == sibling


def test_display_relative_without_plugin_returns_path():
    assert paths.display_relative("/a/b", "") == "/a/b"


@pytest.mark.skipif(os.name != "nt", reason="casse des chemins ignorée seulement sous Windows")
def test_display_relative_ignores_case_on_windows(tmp_path):
    plugin = str(tmp_path / "Plugin.lrplugin")
    target = os.path.join(plugin.upper(), "__i18n_tmp__", "2_Applicator")
    assert paths.display_relative(target, plugin.lower()) == "<plugin>/__i18n_tmp__/2_Applicator"


def _make_outputs(plugin, folder, stamps):
    for stamp in stamps:
        os.makedirs(os.path.join(plugin, "__i18n_tmp__", folder, stamp))


def test_find_all_tool_outputs_ignores_lookalike_folder(tmp_path):
    plugin = str(tmp_path / "p.lrplugin")
    _make_outputs(plugin, "Extractor_old", ["20250101_000000"])
    _make_outputs(plugin, "Extract", ["20250102_000000"])
    assert paths.find_all_tool_outputs(plugin, "Extractor") == []


def test_find_all_tool_outputs_merges_old_and_new_folders(tmp_path):
    plugin = str(tmp_path / "p.lrplugin")
    _make_outputs(plugin, "Extractor", ["20250101_000000"])
    _make_outputs(plugin, "1_Extractor", ["20260101_000000", "not_a_timestamp", "2026010X_000000"])
    found = [os.path.basename(p) for p in paths.find_all_tool_outputs(plugin, "Extractor")]
    assert found == ["20260101_000000", "20250101_000000"]


def test_find_git_root_two_levels_up(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    plugin = repo / "src" / "x.lrplugin"
    plugin.mkdir(parents=True)
    assert os.path.normcase(paths.find_git_root(str(plugin))) == os.path.normcase(str(repo))


def test_gitignore_target_uses_path_relative_to_git_root(tmp_path, isolated_config):
    import LocalizationToolKit

    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    plugin = repo / "src" / "x.lrplugin"
    plugin.mkdir(parents=True)
    config = LocalizationToolKit.ConfigManager(isolated_config)
    gitignore, line = config._gitignore_target(str(plugin))
    assert os.path.normcase(gitignore) == os.path.normcase(str(repo / ".gitignore"))
    assert line == "src/x.lrplugin/__i18n_tmp__/"

    assert config.add_temp_dir_to_gitignore(str(plugin)) is True
    assert "src/x.lrplugin/__i18n_tmp__/" in (repo / ".gitignore").read_text(encoding="utf-8")


def test_run_script_module_name_uses_splitext(tmp_path, monkeypatch, isolated_config):
    import LocalizationToolKit

    script = tmp_path / "tools" / "a.python" / "run.py"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(LocalizationToolKit.subprocess, "run", fake_run)
    launcher = LocalizationToolKit.ToolLauncher(str(tmp_path), LocalizationToolKit.ConfigManager(isolated_config))
    assert launcher._run_script(str(script)) is True
    assert calls[0][1:3] == ["-m", "tools.a.python.run"]


# =============================================================================
# ENCODAGE ET ERREURS
# =============================================================================

def test_applicator_reports_latin1_file_and_continues(plugin_dir, isolated_config):
    from tools.applicator.main import process_plugin_directory
    from tools.extractor.main import run_extraction

    with open(os.path.join(plugin_dir, "Latin.lua"), "w", encoding="latin-1") as f:
        f.write('title = "Caf\xe9"\n')

    run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, False, silent=True)
    success, report = process_plugin_directory(plugin_dir, silent=True)

    assert success is False
    assert any("Latin.lua" in err["file"] for err in report.errors)
    with open(os.path.join(plugin_dir, "ui", "Dialog.lua"), encoding="utf-8") as f:
        assert 'LOC "$$$/Test/' in f.read()


def test_load_replacements_json_respects_silent(plugin_dir, isolated_config, capsys):
    from tools.applicator.main import load_replacements_json, process_plugin_directory
    from tools.extractor.main import run_extraction

    from core.paths import find_latest_tool_output

    run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, True, silent=True)
    capsys.readouterr()
    extraction_dir = find_latest_tool_output(plugin_dir, "Extractor")

    assert load_replacements_json(extraction_dir, silent=True)
    assert capsys.readouterr().out == ""

    process_plugin_directory(plugin_dir, extraction_dir=extraction_dir, dry_run=True, silent=True)
    assert capsys.readouterr().out == ""


def test_load_config_reports_invalid_json(isolated_config, capsys):
    from tools.translator import config_loader

    with open(os.path.join(isolated_config, "config.json"), "w", encoding="utf-8") as f:
        f.write("{ invalide")
    assert config_loader.load_config() == {}
    out = capsys.readouterr()
    assert "config.json" in out.out + out.err


def test_debug_i18n_context_reports_errors(monkeypatch, capsys):
    from core import i18n
    from tools.translator import config_loader

    def boom():
        raise RuntimeError("config cassée")

    monkeypatch.setattr(config_loader, "get_debug_i18n", boom)
    with i18n.debug_i18n_context():
        pass
    assert "config cassée" in capsys.readouterr().err


def test_load_translation_error_goes_to_stderr(monkeypatch, capsys):
    from core import i18n

    def boom(*args, **kwargs):
        raise OSError("catalogue illisible")

    monkeypatch.setattr(i18n.gettext, "translation", boom)
    assert i18n._load_translation("en") is None
    out = capsys.readouterr()
    assert "catalogue illisible" in out.err
    assert "catalogue illisible" not in out.out


def test_generate_loc_key_distinguishes_colon():
    from tools.extractor.utils import generate_loc_key

    assert generate_loc_key("Export:", "PWExport.lua", "$$$/T", set()) != \
        generate_loc_key("Export", "PWExport.lua", "$$$/T", set())
    assert generate_loc_key("Export:", "PWExport.lua", "$$$/T", set()).endswith("ExportColon")


def test_technical_context_patterns_are_used():
    import re

    from tools.extractor.config import PluginRules
    from tools.extractor.utils import is_in_technical_context

    rules = PluginRules(technical_context_patterns=[re.compile(r"X-Custom")])
    assert is_in_technical_context('{ field = "X-Custom", value = "abc" }', rules)
    assert not is_in_technical_context('{ field = "X-Custom", value = "abc" }', PluginRules(technical_context_patterns=[]))


@pytest.mark.parametrize("language", ["fr", "en"])
def test_sync_markers_start_with_machine_constants(tmp_path, language):
    from core import i18n
    from tools.translator.common import MARKER_NEEDS_REVIEW, MARKER_NEW
    from tools.translator.sync import _sync_language

    assert MARKER_NEW == "-- [NEW]"
    assert MARKER_NEEDS_REVIEW == "-- [NEEDS_REVIEW]"

    lang_file = tmp_path / "TranslatedStrings_fr.txt"
    lang_file.write_text('"$$$/T/A=a"\n"$$$/T/B=b"\n', encoding="utf-8")
    ref = {"$$$/T/A": "A", "$$$/T/B": "B2", "$$$/T/C": "C"}
    update_data = {"added": {"$$$/T/C": "C"}, "changed": {"$$$/T/B": {"old": "B", "new": "B2"}}, "deleted": {}}
    with i18n.temporary_language(language):
        _sync_language("fr", str(lang_file), ref, set(ref), {"$$$/T/C"}, {"$$$/T/B"}, set(),
                       str(tmp_path), update_data, str(tmp_path / "bak"))
    lines = lang_file.read_text(encoding="utf-8").splitlines()
    assert any(line.startswith(MARKER_NEW) for line in lines)
    assert any(line.startswith(MARKER_NEEDS_REVIEW) for line in lines)


def test_clean_markers_only_removes_toolkit_markers(tmp_path):
    from tools.translator.autosync import clean_markers_from_file
    from tools.translator.common import MARKER_NEEDS_REVIEW, MARKER_NEW

    target = tmp_path / "TranslatedStrings_fr.txt"
    content = [MARKER_NEW + " À traduire", '"$$$/A=a"', MARKER_NEEDS_REVIEW + " Modifié", '"$$$/B=b"',
               "-- [autre] commentaire", ""]
    target.write_text("\n".join(content), encoding="utf-8")
    clean_markers_from_file(str(target))
    assert target.read_text(encoding="utf-8").splitlines() == ['"$$$/A=a"', '"$$$/B=b"', "-- [autre] commentaire"]


# =============================================================================
# MENU : ANNULER ≠ ERREUR
# =============================================================================

def _answers(monkeypatch, *values):
    it = iter(values)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


def test_select_tool_output_dir_cancel_returns_current(tmp_path, monkeypatch):
    from core.menu_helpers import select_tool_output_dir

    plugin = str(tmp_path / "p.lrplugin")
    os.makedirs(plugin)
    _answers(monkeypatch, "")
    assert select_tool_output_dir(plugin, "Extractor", "/actuel") == "/actuel"


def test_select_tool_output_dir_error_returns_none(tmp_path, monkeypatch):
    from core.menu_helpers import select_tool_output_dir

    plugin = str(tmp_path / "p.lrplugin")
    os.makedirs(plugin)
    _answers(monkeypatch, str(tmp_path / "absent"))
    assert select_tool_output_dir(plugin, "Extractor", "/actuel") is None


# =============================================================================
# COULEURS / TERMINAL
# =============================================================================

COLOR_MODULES = [
    "LocalizationToolKit", "core.menu_helpers", "core.output_formatters",
    "tools.applicator.main", "tools.applicator.menu", "tools.extractor.menu",
    "tools.toolbox.delete_temp_dir", "tools.toolbox.restore_backup", "tools.translator.addlang",
    "tools.translator.autosync", "tools.translator.common", "tools.translator.install", "tools.translator.main",
]


@pytest.mark.parametrize("module_name", COLOR_MODULES)
def test_modules_share_the_color_instance(module_name):
    import importlib

    import core.colors

    module = importlib.import_module(module_name)
    assert module.c is core.colors.c


@pytest.mark.skipif(os.name != "nt", reason="SetConsoleMode n'existe que sous Windows")
def test_supports_color_checks_set_console_mode(monkeypatch):
    import ctypes

    from core import colors

    class FakeKernel32:
        def GetStdHandle(self, n):
            return 1

        def GetConsoleMode(self, handle, mode):
            return 1

        def SetConsoleMode(self, handle, mode):
            return 0

    class FakeWindll:
        kernel32 = FakeKernel32()

    class TtyStdout:
        def isatty(self):
            return True

    for name in ("FORCE_COLOR", "NO_COLOR", "TERM", "WT_SESSION", "ConEmuANSI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(ctypes, "windll", FakeWindll())
    monkeypatch.setattr(colors.sys, "stdout", TtyStdout())
    assert colors.supports_color() is False


def test_flip_anim_is_silent_without_terminal(capsys):
    from assets import flip_anim

    flip_anim.airport_display_intro(duration=0.01, fade_duration=0.01, final_pause=0)
    assert capsys.readouterr().out == ""


def test_flip_anim_respects_no_color(monkeypatch, capsys):
    from assets import flip_anim

    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(flip_anim.sys.stdout, "isatty", lambda: True, raising=False)
    flip_anim.airport_display_intro(duration=0.01, fade_duration=0.01, final_pause=0)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("module_name", ["tools.toolbox.delete_temp_dir", "tools.toolbox.restore_backup"])
def test_toolbox_clear_screen_only_on_terminal(monkeypatch, module_name):
    import importlib

    module = importlib.import_module(module_name)
    calls = []
    monkeypatch.setattr(module.os, "system", lambda cmd: calls.append(cmd))
    module.clear_screen()
    assert calls == []


def test_backup_count_is_recursive(tmp_path):
    from tools.toolbox.restore_backup import count_backup_files

    (tmp_path / "ui").mkdir()
    (tmp_path / "A.lua.bak").write_text("", encoding="utf-8")
    (tmp_path / "ui" / "B.lua.bak").write_text("", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("", encoding="utf-8")
    assert count_backup_files(str(tmp_path)) == 2


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_launcher_help_exits_zero(toolkit_root, flag):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, "LocalizationToolKit.py", flag], cwd=toolkit_root, env=env,
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "LocalizationToolKit.py extract" in result.stdout


def test_extractor_report_paths_use_display_relative():
    from core.output_formatters import OutputFormatter
    from tools.extractor.output import OutputGenerator
    from tools.extractor.report import ReportGenerator

    for helper in (OutputFormatter._extract_relative_path, OutputGenerator._shorten_path,
                   ReportGenerator._shorten_path):
        assert helper("/x/plugin.lrplugin-old/a", "/x/plugin.lrplugin") == "/x/plugin.lrplugin-old/a"
