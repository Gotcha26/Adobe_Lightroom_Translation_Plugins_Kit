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


def test_autosync_applicator_failure_names_the_file(plugin_dir, isolated_config):
    """#25 #32 : l'échec de l'Applicator cite le fichier fautif."""
    with open(os.path.join(plugin_dir, "Latin1.lua"), "wb") as f:
        f.write('local t = { title = "Café crème" }\n'.encode("latin-1"))

    results = run_autosync(plugin_dir, assume_yes=True)

    assert results["errors"]
    assert "Latin1.lua" in results["errors"][0], results["errors"]


def _modify_en_value(plugin_dir):
    """Change une valeur EN du plugin : l'extraction fraîche la verra « modifiée »."""
    en_path = os.path.join(plugin_dir, "TranslatedStrings_en.txt")
    with open(en_path, encoding="utf-8") as f:
        content = f.read()
    content = content.replace('"$$$/Test/Export/Existing=Existing label"',
                              '"$$$/Test/Export/Existing=Previous label"')
    with open(en_path, "w", encoding="utf-8") as f:
        f.write(content)


def test_autosync_backup_keeps_original_translation(plugin_dir, isolated_config):
    """#17 #25 : dans une même session, le premier .bak (l'original) n'est pas écrasé."""
    fr_path = os.path.join(plugin_dir, "TranslatedStrings_fr.txt")
    with open(fr_path, encoding="utf-8") as f:
        original_fr = f.read()
    _modify_en_value(plugin_dir)

    results = run_autosync(plugin_dir, assume_yes=True)
    assert results["errors"] == []

    with open(fr_path, encoding="utf-8") as f:
        assert f.read() != original_fr, "le test suppose que le FR a été modifié"

    applicator_root = os.path.join(plugin_dir, "__i18n_tmp__", "2_Applicator")
    (session,) = os.listdir(applicator_root)
    bak = os.path.join(applicator_root, session, "backups", "TranslatedStrings_fr.txt.bak")
    with open(bak, encoding="utf-8") as f:
        assert f.read() == original_fr


def test_autosync_inject_uses_reference_values(plugin_dir, isolated_config):
    """#25 : sans traduction fournie, INJECT reprend la valeur de référence (UPDATE dans compare/)."""
    _modify_en_value(plugin_dir)

    results = run_autosync(plugin_dir, assume_yes=True)

    assert results["errors"] == []
    assert results["inject"]["fr"]["from_ref"] > 0, results["inject"]


def _session_names(plugin_dir, tool_folder):
    root = os.path.join(plugin_dir, "__i18n_tmp__", tool_folder)
    if not os.path.isdir(root):
        return set()
    return {d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))}


def test_autosync_accepted_confirmation_applies_and_writes_both_reports(
        plugin_dir, isolated_config, monkeypatch, distinct_timestamps):
    """#37 : « o » à la confirmation modifie les .lua ; les deux rapports coexistent."""
    before = _lua_contents(plugin_dir)
    monkeypatch.setattr("builtins.input", lambda *_args: "o")

    results = run_autosync(plugin_dir)

    assert results["errors"] == []
    assert results["applicator"]["lines_to_modify"] > 0
    assert _lua_contents(plugin_dir) != before

    applicator_root = os.path.join(plugin_dir, "__i18n_tmp__", "2_Applicator")
    (session,) = os.listdir(applicator_root)
    assert os.path.isfile(os.path.join(applicator_root, session, "application_report_dry_run.txt"))
    assert os.path.isfile(os.path.join(applicator_root, session, "application_report.txt"))


def test_autosync_refusal_removes_only_the_session_it_created(plugin_dir, isolated_config, monkeypatch,
                                                              distinct_timestamps):
    """#37 : après un refus, ni session neuve ni artefact ; les sessions antérieures restent."""
    old = {}
    for tool_folder in ("1_Extractor", "2_Applicator", "3_Translator"):
        old_session = os.path.join(plugin_dir, "__i18n_tmp__", tool_folder, "20200101_000000")
        os.makedirs(old_session)
        with open(os.path.join(old_session, "keep.txt"), "w", encoding="utf-8") as f:
            f.write("ancien")
        old[tool_folder] = old_session
    before = {folder: _session_names(plugin_dir, folder) for folder in old}
    lua_before = _lua_contents(plugin_dir)
    monkeypatch.setattr("builtins.input", lambda *_args: "n")

    results = run_autosync(plugin_dir)

    assert _("Annulé par l'utilisateur") in results["errors"]
    assert _lua_contents(plugin_dir) == lua_before
    for folder, session in old.items():
        assert _session_names(plugin_dir, folder) == before[folder]
        assert os.path.isfile(os.path.join(session, "keep.txt"))


def test_autosync_refusal_reports_what_was_cleaned(plugin_dir, isolated_config, monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda *_args: "n")

    run_autosync(plugin_dir)

    out = capsys.readouterr().out
    assert _("Session temporaire supprimée") in out


def test_silent_process_plugin_directory_prints_nothing(plugin_dir, isolated_config, capsys):
    """#37 : en mode silencieux, auto-détection ou extraction invalide n'affichent rien."""
    from tools.applicator.main import process_plugin_directory
    from tools.extractor.main import run_extraction

    # Aucune extraction à auto-détecter
    ok, report = process_plugin_directory(plugin_dir, silent=True)
    assert not ok and report.errors

    # Dossier d'extraction invalide
    ok, report = process_plugin_directory(plugin_dir, extraction_dir=os.path.join(plugin_dir, "absent"),
                                          silent=True)
    assert not ok and report.errors

    # Plugin introuvable
    ok, report = process_plugin_directory(os.path.join(plugin_dir, "absent"), silent=True)
    assert not ok and report.errors

    assert capsys.readouterr().out == ""

    # Extraction auto-détectée
    run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, True, silent=True)
    capsys.readouterr()  # la sortie de l'Extractor n'est pas l'objet du test
    ok, _report = process_plugin_directory(plugin_dir, dry_run=True, silent=True)
    assert ok

    assert capsys.readouterr().out == ""

