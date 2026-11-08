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


def test_backup_message_gives_count_and_relative_dir(tmp_path):
    plugin = str(tmp_path / "plug.lrplugin")
    backup_dir = os.path.join(plugin, paths.get_i18n_dir(), "3_Translator", "20260101_101010", "backups")
    os.makedirs(os.path.join(backup_dir, "sub"))
    for rel in ("a.txt.bak", os.path.join("sub", "b.txt.bak"), "ignored.txt"):
        with open(os.path.join(backup_dir, rel), "w", encoding="utf-8") as f:
            f.write("x")

    message = paths.format_backup_message(backup_dir, plugin)

    assert "2" in message
    assert "<plugin>/" + paths.get_i18n_dir() + "/3_Translator/20260101_101010/backups" in message
    assert plugin not in message
