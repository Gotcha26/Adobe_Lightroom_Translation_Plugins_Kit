"""Non-régression #36 : sessions reconnues au motif exact, repli des sauvegardes, messages précis."""

import os

from core import paths
from tools.toolbox import delete_temp_dir, restore_backup
from tools.translator.inject import run_inject


def _make_session(kit, tool_dir, stamp, with_bak=True):
    backups = os.path.join(kit, tool_dir, stamp, "backups")
    os.makedirs(backups)
    if with_bak:
        with open(os.path.join(backups, "Info.lua.bak"), "w", encoding="utf-8") as f:
            f.write("x")
    return backups


def test_notes_folder_is_not_a_session(tmp_path):
    plugin = str(tmp_path / "plug.lrplugin")
    kit = paths.get_i18n_kit_path(plugin)
    # Dossier d'utilisateur dont le nom contient « applicator », avec une arborescence de session
    _make_session(kit, "my_applicator_notes", "20260101_101010")
    real = _make_session(kit, "2_Applicator", "20260102_101010")

    sessions = restore_backup.find_applicator_sessions(plugin)
    assert sessions == [("20260102_101010", real)]

    deletable = delete_temp_dir.find_backup_dirs(kit)
    assert [b["session"] for b in deletable] == ["20260102_101010"]


def test_real_sessions_listed_with_and_without_prefix(tmp_path):
    plugin = str(tmp_path / "plug.lrplugin")
    kit = paths.get_i18n_kit_path(plugin)
    _make_session(kit, "2_Applicator", "20260102_101010")
    _make_session(kit, "Applicator", "20260103_101010")
    # Nom de session qui n'a pas la forme YYYYMMDD_HHMMSS
    _make_session(kit, "2_Applicator", "2026010x_101010")

    sessions = restore_backup.find_applicator_sessions(plugin)
    assert [s[0] for s in sessions] == ["20260103_101010", "20260102_101010"]
    assert [b["session"] for b in delete_temp_dir.find_backup_dirs(kit)] == [
        "20260103_101010", "20260102_101010"]


def test_fallback_backup_never_at_plugin_root(isolated_config, tmp_path):
    # Sans backup_dir de session ni chemin de plugin, la cible est à la racine du plugin
    plugin = tmp_path / "plug.lrplugin"
    plugin.mkdir()
    target = plugin / "TranslatedStrings_fr.txt"
    target.write_text('"$$$/Test/A" = "ancien"\n', encoding="utf-8")
    translate = tmp_path / "TRANSLATE_fr.txt"
    translate.write_text("[KEY] $$$/Test/A\n[EN]  x\n[FR] → nouveau\n", encoding="utf-8")

    run_inject(str(translate), str(target), update_dir=str(tmp_path), backup_dir=None)

    assert not (plugin / "backups").exists()
    assert not list(plugin.glob("*.bak"))
    fallback = plugin / paths.get_i18n_dir() / "backups" / "TranslatedStrings_fr.txt.bak"
    assert fallback.is_file()


def test_fallback_backup_dir_is_under_temp_dir(tmp_path):
    plugin = str(tmp_path / "plug.lrplugin")
    assert paths.fallback_backup_dir(plugin) == os.path.join(plugin, paths.get_i18n_dir(), "backups")
    assert paths.local_backup_path(os.path.join(plugin, "Info.lua")) == os.path.join(
        paths.fallback_backup_dir(plugin), "Info.lua.bak")


def _write(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def test_backup_message_counts_only_files_backed_up_by_this_operation(tmp_path):
    plugin = str(tmp_path / "plug.lrplugin")
    backup_dir = os.path.join(plugin, paths.get_i18n_dir(), "3_Translator", "20260101_101010", "backups")
    # .bak laissé par une opération précédente de la même session : ne doit pas être compté
    _write(os.path.join(backup_dir, "old.txt.bak"))
    for rel in ("a.txt", os.path.join("sub", "b.txt")):
        _write(os.path.join(plugin, rel))

    backups = paths.BackupReport()
    for rel in ("a.txt", os.path.join("sub", "b.txt")):
        paths.backup_once(os.path.join(plugin, rel), plugin, backup_dir, backups)
    message = paths.format_backup_message(backups, plugin)

    assert "2 fichier(s)" in message
    assert "<plugin>/" + paths.get_i18n_dir() + "/3_Translator/20260101_101010/backups" in message
    assert plugin not in message


def test_backup_message_rerun_reports_nothing_new(tmp_path):
    plugin = str(tmp_path / "plug.lrplugin")
    backup_dir = os.path.join(plugin, "bk")
    _write(os.path.join(plugin, "a.txt"))
    paths.backup_once(os.path.join(plugin, "a.txt"), plugin, backup_dir)

    backups = paths.BackupReport()
    paths.backup_once(os.path.join(plugin, "a.txt"), plugin, backup_dir, backups)

    assert backups.files == []
    assert "0 fichier" not in paths.format_backup_message(backups, plugin)


def test_sync_after_inject_in_same_session_reports_only_its_own_backups(isolated_config, plugin_dir, tmp_path):
    from tools.translator.sync import run_sync

    session_backups = os.path.join(plugin_dir, paths.get_i18n_dir(), "3_Translator", "20260101_101010", "backups")
    translate = tmp_path / "TRANSLATE_fr.txt"
    translate.write_text("[KEY] $$$/Test/A\n[EN]  x\n[FR] → nouveau\n", encoding="utf-8")
    target = os.path.join(plugin_dir, "TranslatedStrings_fr.txt")

    inject_backups = paths.BackupReport()
    run_inject(str(translate), target, str(tmp_path), backup_dir=session_backups, backups=inject_backups)
    assert len(inject_backups.files) == 1

    sync_backups = paths.BackupReport()
    run_sync(os.path.join(plugin_dir, "TranslatedStrings_en.txt"), plugin_dir, None, session_backups, sync_backups)
    assert sync_backups.files == []


def test_run_sync_exposes_the_fallback_folder_it_used(isolated_config, plugin_dir):
    from tools.translator.sync import run_sync

    backups = paths.BackupReport()
    run_sync(os.path.join(plugin_dir, "TranslatedStrings_en.txt"), plugin_dir, None, None, backups)

    assert backups.directory == paths.fallback_backup_dir(plugin_dir)
    assert backups.files and all(os.path.isfile(f) for f in backups.files)
    assert f"{len(backups.files)} fichier(s)" in paths.format_backup_message(backups, plugin_dir)


def test_applicator_fallback_backup_stays_in_one_plugin_level_folder(isolated_config, plugin_dir):
    from tools.applicator.main import LocalizationReport, load_replacements_json, process_file_with_replacements
    from tools.extractor.main import run_extraction

    out = run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, False, silent=True)
    extraction_dir = out if isinstance(out, str) else paths.find_latest_tool_output(plugin_dir, "Extractor")
    files_data = load_replacements_json(extraction_dir, silent=True)["files"]
    rel = os.path.join("ui", "Dialog.lua")
    key = next(k for k in files_data if os.path.normpath(k) == rel)

    report = LocalizationReport("plug")
    process_file_with_replacements(os.path.join(plugin_dir, rel), files_data[key], report, False,
                                   backup_dir=None, create_backup=True, plugin_path=plugin_dir)

    subfolder = os.path.join(plugin_dir, "ui")
    assert not [f for f in os.listdir(subfolder) if f.endswith(".bak")]
    assert paths.get_i18n_dir() not in os.listdir(subfolder)
    assert os.path.isfile(os.path.join(paths.fallback_backup_dir(plugin_dir), rel + ".bak"))
