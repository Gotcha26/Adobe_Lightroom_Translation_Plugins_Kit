"""Non-régression AUTOSYNC (#11, #25).

- #11 : les noms de fichiers ne doivent plus être corrompus.
- #25 : préfixe lu dans la configuration, confirmation avant l'Applicator réel,
  une seule session Applicator par exécution.
"""

import os
import re
from datetime import datetime as _real_datetime, timedelta

import pytest

from core.i18n import _
from tools.translator.autosync import run_autosync


@pytest.fixture
def distinct_timestamps(monkeypatch):
    """Chaque appel à get_tool_output_path obtient un horodatage distinct.

    Sans cela, deux sessions créées dans la même seconde partageraient le même
    dossier et masqueraient la création de sessions en double.
    """
    import core.paths

    class _TickingDatetime:
        calls = 0

        @classmethod
        def now(cls):
            cls.calls += 1
            return _real_datetime(2026, 1, 1, 12, 0, 0) + timedelta(seconds=cls.calls)

    monkeypatch.setattr(core.paths, "datetime", _TickingDatetime)


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


def test_autosync_runs_on_fixture(plugin_dir, isolated_config):
    results = run_autosync(plugin_dir, assume_yes=True)

    assert results["errors"] == []
    assert os.path.isfile(results["extractor"]["en_file"])

    corrupted = [
        name
        for _root, _dirs, files in os.walk(plugin_dir)
        for name in files
        if name.startswith("_(")
    ]
    assert corrupted == []


def test_autosync_uses_configured_prefix(plugin_dir, isolated_config):
    results = run_autosync(plugin_dir, assume_yes=True)
    assert results["errors"] == []

    with open(results["extractor"]["en_file"], encoding="utf-8") as f:
        keys = re.findall(r'^"(\$\$\$/[^=]+)=', f.read(), flags=re.MULTILINE)

    assert keys
    assert all(key.startswith("$$$/Test/") for key in keys), keys


def test_autosync_creates_single_applicator_session(plugin_dir, isolated_config, distinct_timestamps):
    results = run_autosync(plugin_dir, assume_yes=True)
    assert results["errors"] == []

    applicator_root = os.path.join(plugin_dir, "__i18n_tmp__", "2_Applicator")
    sessions = [d for d in os.listdir(applicator_root) if os.path.isdir(os.path.join(applicator_root, d))]
    assert len(sessions) == 1, sessions


@pytest.mark.parametrize(("extra_args", "expected"), [([], False), (["--yes"], True)])
def test_translator_cli_autosync_passes_assume_yes_only_with_yes(plugin_dir, monkeypatch, extra_args, expected):
    import sys

    from tools.translator import main as translator_main

    calls = []
    monkeypatch.setattr(translator_main, "run_autosync",
                        lambda path, **kwargs: calls.append(kwargs) or {"errors": [], "sync": {}})
    monkeypatch.setattr(translator_main, "print_autosync_report", lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["main.py", "autosync", "--plugin-path", plugin_dir, *extra_args])

    with pytest.raises(SystemExit) as exc:
        translator_main.main()

    assert exc.value.code == 0
    assert calls == [{"assume_yes": expected}]


@pytest.mark.parametrize(("extra_args", "expected"), [([], []), (["--yes"], ["--yes"])])
def test_toolkit_cli_autosync_forwards_yes_only_when_given(plugin_dir, isolated_config, monkeypatch,
                                                           extra_args, expected):
    import LocalizationToolKit

    captured = []
    monkeypatch.setattr(LocalizationToolKit.ToolLauncher, "_run_script",
                        lambda self, script, args=None, cwd=None: captured.append(args) or True)
    monkeypatch.setattr(LocalizationToolKit.ConfigManager, "get",
                        lambda self, key, default=None: plugin_dir if key == "plugin_path" else default)
    monkeypatch.setattr("sys.argv", ["LocalizationToolKit.py", "autosync", *extra_args])

    with pytest.raises(SystemExit) as exc:
        LocalizationToolKit.main()

    assert exc.value.code == 0
    assert captured == [["autosync", "--plugin-path", plugin_dir, *expected]]


def test_autosync_closed_stdin_counts_as_refusal(plugin_dir, isolated_config, monkeypatch):
    before = _lua_contents(plugin_dir)

    def closed_stdin(*_args):
        raise EOFError

    monkeypatch.setattr("builtins.input", closed_stdin)

    results = run_autosync(plugin_dir)

    assert results["errors"] == [_("Annulé par l'utilisateur")]
    assert _lua_contents(plugin_dir) == before


def test_autosync_first_install_points_to_install(plugin_dir, isolated_config, capsys):
    for name in os.listdir(plugin_dir):
        if name.startswith("TranslatedStrings_"):
            os.remove(os.path.join(plugin_dir, name))

    run_autosync(plugin_dir, assume_yes=True)

    out = capsys.readouterr().out
    assert _("  → Utilisez la commande INSTALL pour installer les fichiers depuis l'extraction") in out


def test_extractor_missing_plugin_raises_file_not_found(tmp_path):
    from tools.extractor.main import run_extraction

    with pytest.raises(FileNotFoundError):
        run_extraction(str(tmp_path / "absent"), "", "$$$/Test", "en", [], 3, True, silent=True)


def test_autosync_refusal_leaves_lua_untouched(plugin_dir, isolated_config, monkeypatch):
    before = _lua_contents(plugin_dir)
    monkeypatch.setattr("builtins.input", lambda *_args: "n")

    results = run_autosync(plugin_dir)

    assert _("Annulé par l'utilisateur") in results["errors"]
    assert _lua_contents(plugin_dir) == before
