"""Tests de ConfigManager : séparation config.json / config.local.json (#18)."""

import json

import LocalizationToolKit as ltk
from LocalizationToolKit import ConfigManager


def _write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")


def test_set_with_local_file_leaves_shared_untouched(tmp_path):
    shared = {"lang": "fr", "prefix": "$$$/Test"}
    _write(tmp_path / "config.json", shared)
    _write(tmp_path / "config.local.json", {"debug_i18n": True})
    before = (tmp_path / "config.json").read_text(encoding="utf-8")

    cm = ConfigManager(str(tmp_path))
    cm.set("enable_flip_anim", False)

    assert (tmp_path / "config.json").read_text(encoding="utf-8") == before
    local = json.loads((tmp_path / "config.local.json").read_text(encoding="utf-8"))
    assert local == {"debug_i18n": True, "enable_flip_anim": False}
    assert cm.get("enable_flip_anim") is False
    assert cm.get("lang") == "fr"


def test_set_without_local_file_writes_shared(tmp_path):
    _write(tmp_path / "config.json", {"lang": "fr"})

    cm = ConfigManager(str(tmp_path))
    cm.set("enable_flip_anim", False)

    assert not (tmp_path / "config.local.json").exists()
    shared = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert shared["enable_flip_anim"] is False
    assert shared["lang"] == "fr"
    assert "last_used" not in shared
    # Les valeurs par défaut ne sont pas recopiées dans le fichier
    assert "plugin_path" not in shared


def test_default_plugin_path_is_empty():
    assert ltk.DEFAULT_CONFIG["plugin_path"] == ""
