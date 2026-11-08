"""Emplacement des sorties du Translator (#28)."""

import glob
import os

from core.paths import find_latest_update_dir, get_tool_output_path
from tools.translator.compare import run_compare
from tools.translator.compare_langs import run_compare_langs
from tools.translator.config_loader import get_update_filename
from tools.translator.inject import run_inject
from tools.translator.sync import run_sync


def _langs(plugin_dir):
    return (
        os.path.join(plugin_dir, "TranslatedStrings_en.txt"),
        os.path.join(plugin_dir, "TranslatedStrings_fr.txt"),
    )


def _bak_files(root):
    return glob.glob(os.path.join(root, "**", "*.bak"), recursive=True)


def test_find_latest_update_dir_skips_compare_langs(isolated_config, plugin_dir):
    en, fr = _langs(plugin_dir)
    tool_dir = os.path.dirname(get_tool_output_path(plugin_dir, "Translator", create=True))
    run_compare(en, fr, os.path.join(tool_dir, "20990101_000000"))
    run_compare_langs(en, fr, None, None, os.path.join(tool_dir, "20990101_000001"))
    # le dernier dossier est un COMPARE-LANGS : l'UPDATE valide est dans le précédent
    expected = os.path.join(tool_dir, "20990101_000000")
    assert find_latest_update_dir(plugin_dir, get_update_filename()) == expected


def test_find_latest_update_dir_prefers_newest_compare(isolated_config, plugin_dir):
    en, fr = _langs(plugin_dir)
    tool_dir = os.path.dirname(get_tool_output_path(plugin_dir, "Translator", create=True))
    run_compare(en, fr, os.path.join(tool_dir, "20990101_000000"))
    run_compare_langs(en, fr, None, None, os.path.join(tool_dir, "20990101_000001"))
    run_compare(en, fr, os.path.join(tool_dir, "20990101_000002"))
    assert find_latest_update_dir(plugin_dir, get_update_filename()) == os.path.join(tool_dir, "20990101_000002")


def test_find_latest_update_dir_finds_compare_subfolder(isolated_config, plugin_dir):
    en, fr = _langs(plugin_dir)
    tool_dir = os.path.dirname(get_tool_output_path(plugin_dir, "Translator", create=True))
    sub = os.path.join(tool_dir, "20990101_000000", "compare")
    run_compare(en, fr, sub)
    assert find_latest_update_dir(plugin_dir, get_update_filename()) == sub


def test_find_latest_update_dir_none(isolated_config, plugin_dir):
    assert find_latest_update_dir(plugin_dir, get_update_filename()) is None


def test_compare_without_output_dir_uses_tempdir(isolated_config, plugin_dir, toolkit_root):
    en, fr = _langs(plugin_dir)
    out = run_compare(en, fr)
    out2 = run_compare_langs(en, fr)
    try:
        for path in (out, out2):
            assert os.path.basename(path).startswith("i18n_kit_")
            assert not os.path.abspath(path).startswith(os.path.join(toolkit_root, "tools"))
    finally:
        import shutil
        shutil.rmtree(out, ignore_errors=True)
        shutil.rmtree(out2, ignore_errors=True)


def test_sync_without_backup_dir_leaves_plugin_root_clean(isolated_config, plugin_dir):
    run_sync(os.path.join(plugin_dir, "TranslatedStrings_en.txt"), plugin_dir, None)
    assert glob.glob(os.path.join(plugin_dir, "*.bak")) == []
    assert os.path.isfile(os.path.join(plugin_dir, "__i18n_tmp__", "backups", "TranslatedStrings_fr.txt.bak"))


def test_inject_without_backup_dir_leaves_target_dir_clean(isolated_config, plugin_dir, tmp_path):
    translate = tmp_path / "TRANSLATE_fr.txt"
    translate.write_text("", encoding="utf-8")
    target = os.path.join(plugin_dir, "TranslatedStrings_fr.txt")
    run_inject(str(translate), target, str(tmp_path))
    assert glob.glob(os.path.join(plugin_dir, "*.bak")) == []
    assert _bak_files(plugin_dir) in ([], [os.path.join(plugin_dir, "__i18n_tmp__", "backups", "TranslatedStrings_fr.txt.bak")])
