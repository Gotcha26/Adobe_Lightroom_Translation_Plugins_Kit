"""Non-régression #17 : les backups conservent l'arborescence relative et sont restaurés en place."""

import os

from core.paths import backup_path_for
from tools.applicator.main import process_plugin_directory
from tools.extractor.main import run_extraction
from tools.toolbox import restore_backup


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_backup_path_for_keeps_relative_tree(tmp_path):
    plugin = str(tmp_path / "plug")
    result = backup_path_for(os.path.join(plugin, "ui", "Dialog.lua"), plugin, str(tmp_path / "bk"))
    assert result == os.path.join(str(tmp_path / "bk"), "ui", "Dialog.lua.bak")


def test_backup_path_for_root_file(tmp_path):
    plugin = str(tmp_path / "plug")
    result = backup_path_for(os.path.join(plugin, "Info.lua"), plugin, str(tmp_path / "bk"))
    assert result == os.path.join(str(tmp_path / "bk"), "Info.lua.bak")


def test_same_basename_backups_and_restore(plugin_dir, isolated_config):
    originals = {
        rel: _read(os.path.join(plugin_dir, rel))
        for rel in (os.path.join("ui", "Dialog.lua"), os.path.join("api", "Dialog.lua"))
    }

    run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, False, silent=True)
    assert process_plugin_directory(plugin_dir, silent=True)

    for rel in originals:
        assert _read(os.path.join(plugin_dir, rel)) != originals[rel]

    sessions = restore_backup.find_applicator_sessions(plugin_dir)
    assert sessions
    backup_dir = sessions[0][1]
    for rel, original in originals.items():
        assert _read(os.path.join(backup_dir, rel + ".bak")) == original

    pairs = restore_backup.find_backup_pairs_in_dir(backup_dir, plugin_dir)
    assert restore_backup.restore_files(pairs) == len(pairs)

    for rel, original in originals.items():
        assert _read(os.path.join(plugin_dir, rel)) == original
    assert not os.path.exists(os.path.join(plugin_dir, "Dialog.lua"))


def test_legacy_flat_backup_still_restores_at_root(tmp_path):
    plugin = tmp_path / "plug"
    backup = tmp_path / "bk"
    plugin.mkdir()
    backup.mkdir()
    (backup / "Info.lua.bak").write_text("x", encoding="utf-8")
    pairs = restore_backup.find_backup_pairs_in_dir(str(backup), str(plugin))
    assert pairs == [(os.path.join(str(plugin), "Info.lua"), os.path.join(str(backup), "Info.lua.bak"))]
