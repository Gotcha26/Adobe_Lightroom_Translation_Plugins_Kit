"""Dette de tests et petites incohérences (#39) : suites de la PR #33."""

import json
import os
import shutil
import sys

import pytest

from core import i18n
from tools.translator.inject import parse_translate_file, run_inject

FR_FILE = "TranslatedStrings_fr.txt"
EN_FILE = "TranslatedStrings_en.txt"


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


# =============================================================================
# parse_translate_file : flèche lue via TRANSLATE_ARROW, début de ligne seulement
# =============================================================================

def test_reference_value_starting_with_arrow_is_read(isolated_config, tmp_path):
    """Une valeur de référence « → Suivant » ne devient pas une traduction."""
    p = tmp_path / "TRANSLATE_fr.txt"
    _write(str(p), "[KEY] $$$/A/next\n[EN]  → Next\n[FR] → \n\n"
                   "[KEY] $$$/A/other\n[EN]  Plain\n[FR] → Autre\n")
    result = parse_translate_file(str(p), None)
    assert result["$$$/A/next"] == "→ Next"
    assert result["$$$/A/other"] == "Autre"


def test_translation_containing_arrow_is_kept_whole(isolated_config, tmp_path):
    p = tmp_path / "TRANSLATE_fr.txt"
    _write(str(p), "[KEY] $$$/A/b\n[EN]  Go\n[FR] → Aller → là\n")
    assert parse_translate_file(str(p), None)["$$$/A/b"] == "Aller → là"


def test_target_equal_to_reference_language(isolated_config, tmp_path):
    """Cible = langue de référence : « [EN] → » reste une ligne cible, « [EN]  » la valeur."""
    p = tmp_path / "TRANSLATE_en.txt"
    _write(str(p), "[KEY] $$$/A/b\n[EN]  Source text\n[EN] → \n\n"
                   "[KEY] $$$/A/c\n[EN]  Other\n[EN] → Custom\n")
    result = parse_translate_file(str(p), None)
    assert result["$$$/A/b"] == "Source text"
    assert result["$$$/A/c"] == "Custom"


def test_target_marker_without_trailing_space(isolated_config, tmp_path):
    """« [XX] → » sans espace final (éditeur qui supprime les espaces) : valeur de référence."""
    p = tmp_path / "TRANSLATE_fr.txt"
    _write(str(p), "[KEY] $$$/A/b\n[EN]  Hello\n[FR] →\n\n[KEY] $$$/A/c\n[EN]  Bye\n[FR] →Au revoir\n")
    result = parse_translate_file(str(p), None)
    assert result["$$$/A/b"] == "Hello"
    assert result["$$$/A/c"] == "Au revoir"


# =============================================================================
# ngettext : repli pour la langue source (français)
# =============================================================================

@pytest.mark.parametrize(("n", "expected"), [(0, "fichier"), (1, "fichier"), (2, "fichiers")])
def test_ngettext_source_language_french_rule(monkeypatch, n, expected):
    monkeypatch.setattr(i18n, "_translation", None)
    assert i18n.ngettext("fichier", "fichiers", n) == expected


# =============================================================================
# INJECT : marqueur conservé, sauvegarde, CLI
# =============================================================================

def _fr_with_marker(plugin_dir):
    target = os.path.join(plugin_dir, FR_FILE)
    text = _read(target).replace(
        '"$$$/Test/Export/Old=', '-- [NEEDS_REVIEW] Texte de référence modifié\n"$$$/Test/Export/Old=')
    _write(target, text)
    return target


def test_existing_marker_survives_inject(isolated_config, plugin_dir, tmp_path):
    target = _fr_with_marker(plugin_dir)
    translate = tmp_path / "TRANSLATE_fr.txt"
    _write(str(translate), "[KEY] $$$/Test/Export/Old\n[EN]  Old value\n[FR] → Nouvelle valeur\n")

    run_inject(str(translate), target, create_backup=False)

    text = _read(target)
    assert '"$$$/Test/Export/Old=Nouvelle valeur"' in text
    assert "-- [NEEDS_REVIEW] Texte de référence modifié\n\"$$$/Test/Export/Old=Nouvelle valeur\"" in text


def test_inject_backup_holds_original_content(isolated_config, plugin_dir, tmp_path):
    from core.paths import BackupReport

    target = os.path.join(plugin_dir, FR_FILE)
    original = _read(target)
    translate = tmp_path / "TRANSLATE_fr.txt"
    _write(str(translate), "[KEY] $$$/Test/Export/Old\n[EN]  Old\n[FR] → Changée\n")
    backups = BackupReport()

    run_inject(str(translate), target, backups=backups)

    assert _read(target) != original
    assert len(backups.files) == 1
    assert _read(backups.files[0]) == original
    assert "Ancienne valeur" in _read(backups.files[0])


def test_cli_inject_reports_from_ref(isolated_config, plugin_dir, tmp_path, monkeypatch, capsys):
    """#15 : la sous-commande `inject` lit `from_ref` dans les statistiques."""
    from tools.translator import main as translator_main

    update = tmp_path / "update"
    update.mkdir()
    _write(str(update / "UPDATE_en.json"),
           json.dumps({"added": {"$$$/Test/Export/Fresh": "Fresh value"}, "changed": {}, "deleted": []}))
    translate = tmp_path / "TRANSLATE_fr.txt"
    _write(str(translate), "[KEY] $$$/Test/Export/Fresh\n[EN]  Fresh value\n[FR] → \n")
    target = os.path.join(plugin_dir, FR_FILE)
    monkeypatch.setattr(sys, "argv", ["main.py", "inject", "--translate", str(translate),
                                      "--target", target, "--update", str(update)])

    translator_main.main()

    out = capsys.readouterr().out
    assert "Erreur" not in out and "Error" not in out
    assert '"$$$/Test/Export/Fresh=Fresh value"' in _read(target)
    assert "0" in out and "1" in out  # 0 traduite, 1 valeur de référence


# =============================================================================
# SYNC depuis le menu (#14)
# =============================================================================

def test_menu_sync_without_selection_asks_update_dir(isolated_config, plugin_dir, tmp_path, monkeypatch, capsys):
    """Sans dossier sélectionné, get_update_filename() est appelé sans NameError."""
    from tools.translator import sync

    update = tmp_path / "update"
    update.mkdir()
    shutil.copy(os.path.join(plugin_dir, EN_FILE), str(update / EN_FILE))
    monkeypatch.setattr("core.menu_helpers.select_tool_output_dir", lambda *a, **k: None)
    answers = iter(["o", str(update), plugin_dir, ""])
    monkeypatch.setattr("builtins.input", lambda *_a: next(answers, ""))
    monkeypatch.setattr(sync, "clear_screen", lambda: None, raising=False)

    results = sync.menu_sync(plugin_dir)

    out = capsys.readouterr().out
    assert "UPDATE_en.json" in out
    assert results and "fr" in results


# =============================================================================
# .i18n_kit.json mal formé
# =============================================================================

def test_malformed_rules_json_warns_and_uses_defaults(tmp_path, capsys):
    from tools.extractor.config import PluginRules, load_plugin_rules

    _write(str(tmp_path / ".i18n_kit.json"), "{ not json")
    rules = load_plugin_rules(str(tmp_path))
    assert rules.ignore_exact == PluginRules().ignore_exact
    assert rules.strip_file_prefixes == []
    assert ".i18n_kit.json" in capsys.readouterr().out


def test_rules_json_wrong_root_type_warns(tmp_path, capsys):
    from tools.extractor.config import PluginRules, load_plugin_rules

    _write(str(tmp_path / ".i18n_kit.json"), json.dumps(["ignore_exact"]))
    rules = load_plugin_rules(str(tmp_path))
    assert rules.ignore_exact == PluginRules().ignore_exact
    assert ".i18n_kit.json" in capsys.readouterr().out


def test_rules_json_wrong_field_type_warns(tmp_path, capsys):
    from tools.extractor.config import PluginRules, load_plugin_rules

    _write(str(tmp_path / ".i18n_kit.json"),
           json.dumps({"ignore_exact": "Piwigo Publisher", "strip_file_prefixes": ["PW"]}))
    rules = load_plugin_rules(str(tmp_path))
    assert rules.ignore_exact == PluginRules().ignore_exact
    assert rules.strip_file_prefixes == ["PW"]
    assert "ignore_exact" in capsys.readouterr().out


# =============================================================================
# Fixture isolated_config : isole aussi LocalizationToolKit.ConfigManager
# =============================================================================

def test_isolated_config_isolates_config_manager(isolated_config, toolkit_root):
    import LocalizationToolKit

    manager = LocalizationToolKit.ConfigManager()
    assert os.path.dirname(os.path.abspath(manager.config_path)) == os.path.abspath(isolated_config)
    assert os.path.abspath(isolated_config) != os.path.abspath(toolkit_root)


# =============================================================================
# is_technical_string sur texte dés-échappé
# =============================================================================

def test_technical_string_applies_to_unescaped_text():
    """Choix accepté (#30) : « error\\n » dés-échappé est filtré comme « error »."""
    from tools.extractor.utils import is_technical_string, unescape_lua_string

    assert is_technical_string("error") is True
    assert is_technical_string(unescape_lua_string("error\\n")) is True
    assert is_technical_string("error\n") is True
    # une vraie phrase finissant par un saut de ligne reste extraite
    assert is_technical_string(unescape_lua_string("Impossible d'ouvrir le fichier\\n")) is False
