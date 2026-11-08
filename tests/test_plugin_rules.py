"""Règles d'extraction par plugin via .i18n_kit.json optionnel (#27)."""

import json
import os

from core.defaults import DEFAULT_PREFIX
from tools.extractor.config import PluginRules, load_plugin_rules
from tools.extractor.engine import LocalizableStringExtractor
from tools.extractor.utils import generate_loc_key, is_technical_string

RULES_FILE = ".i18n_kit.json"


def _write_rules(folder, data):
    with open(os.path.join(folder, RULES_FILE), "w", encoding="utf-8") as f:
        json.dump(data, f)


def _categories(plugin_dir):
    extractor = LocalizableStringExtractor(plugin_dir, prefix="$$$/Test")
    extractor.extract_all()
    return {e.suggested_key.split("/")[2] for e in extractor.extracted if e.file_name == "PWExport.lua"}


def test_default_prefix_is_generic():
    assert DEFAULT_PREFIX == "$$$/Plugin"
    assert "Piwigo" not in DEFAULT_PREFIX


def test_without_rules_category_keeps_pw_prefix(plugin_dir):
    os.remove(os.path.join(plugin_dir, RULES_FILE))
    assert "PWExport" in _categories(plugin_dir)


def test_with_strip_file_prefixes_category_is_stripped(plugin_dir):
    _write_rules(plugin_dir, {"strip_file_prefixes": ["PW"]})
    cats = _categories(plugin_dir)
    assert "Export" in cats and "PWExport" not in cats


def test_fixture_ships_its_own_rules(plugin_dir):
    cats = _categories(plugin_dir)
    assert "Export" in cats and "PWExport" not in cats


def test_piwigo_publisher_ignored_only_when_listed(tmp_path):
    empty = load_plugin_rules(str(tmp_path))
    assert isinstance(empty, PluginRules)
    assert not is_technical_string("Piwigo Publisher", None, empty)
    _write_rules(str(tmp_path), {"ignore_exact": ["Piwigo Publisher"]})
    listed = load_plugin_rules(str(tmp_path))
    assert is_technical_string("Piwigo Publisher", None, listed)


def test_regex_rules_are_compiled_and_merged(tmp_path):
    _write_rules(str(tmp_path), {
        "technical_patterns": [r"^pwg\."],
        "ignore_loc_key_patterns": [r"/Accept$"],
        "ignore_loc_values": ["User-Agent"],
    })
    rules = load_plugin_rules(str(tmp_path))
    assert is_technical_string("pwg.session.login", None, rules)
    assert not is_technical_string("pwg.session.login", None, load_plugin_rules(str(tmp_path / "x")))
    assert rules.ignore_loc_key_patterns[0].search("$$$/A/Accept")
    assert "User-Agent" in rules.ignore_loc_values
    # les règles génériques restent présentes
    assert is_technical_string("application/json", None, rules)


def test_generate_loc_key_strip_prefixes_default_empty():
    assert generate_loc_key("Hello world", "PWExport.lua", "$$$/T", set()).split("/")[2] == "PWExport"
    key = generate_loc_key("Hello world", "PWExport.lua", "$$$/T", set(), ["PW"])
    assert key.split("/")[2] == "Export"


def test_example_file_is_valid(toolkit_root):
    path = os.path.join(toolkit_root, "doc", "examples", RULES_FILE)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert "Piwigo Publisher" in data["ignore_exact"]
    assert data["strip_file_prefixes"] == ["PW", "Piwigo"]
