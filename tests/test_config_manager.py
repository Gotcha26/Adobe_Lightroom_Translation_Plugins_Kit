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


def test_set_without_local_file_creates_local_shared_untouched(tmp_path):
    _write(tmp_path / "config.json", {"lang": "fr"})
    before = (tmp_path / "config.json").read_text(encoding="utf-8")

    cm = ConfigManager(str(tmp_path))
    cm.set("enable_flip_anim", False)

    assert (tmp_path / "config.json").read_text(encoding="utf-8") == before
    local = json.loads((tmp_path / "config.local.json").read_text(encoding="utf-8"))
    # Seule la valeur modifiée est écrite : ni config.json ni les défauts ne sont recopiés
    assert local == {"enable_flip_anim": False}
    assert cm.get("enable_flip_anim") is False
    assert cm.get("lang") == "fr"


def test_set_with_invalid_json_local_file_does_not_overwrite(tmp_path, capsys):
    _write(tmp_path / "config.json", {"lang": "fr"})
    raw = b'{"plugin_path": "C:/mon/plugin", '  # JSON tronqué
    (tmp_path / "config.local.json").write_bytes(raw)

    cm = ConfigManager(str(tmp_path))
    cm.set("enable_flip_anim", False)

    assert (tmp_path / "config.local.json").read_bytes() == raw
    assert cm.get("enable_flip_anim") is False  # appliqué en mémoire
    assert "config.local.json" in capsys.readouterr().out


def test_set_with_list_root_local_file_does_not_overwrite(tmp_path):
    _write(tmp_path / "config.json", {"lang": "fr"})
    (tmp_path / "config.local.json").write_bytes(b"[]")

    cm = ConfigManager(str(tmp_path))
    cm.set("enable_flip_anim", False)

    assert (tmp_path / "config.local.json").read_bytes() == b"[]"
    assert cm.get("enable_flip_anim") is False


def test_set_with_undecodable_local_file_does_not_overwrite(tmp_path):
    raw = b'{"plugin_path": "\xff\xfe"}'  # UTF-8 invalide
    (tmp_path / "config.local.json").write_bytes(raw)

    cm = ConfigManager(str(tmp_path))
    cm.set("enable_flip_anim", False)

    assert (tmp_path / "config.local.json").read_bytes() == raw


def test_set_with_valid_local_file_merges_and_keeps_other_keys(tmp_path):
    _write(tmp_path / "config.local.json", {"plugin_path": "C:/p", "lang": "de"})

    cm = ConfigManager(str(tmp_path))
    cm.set("enable_flip_anim", False)

    local = json.loads((tmp_path / "config.local.json").read_text(encoding="utf-8"))
    assert local == {"plugin_path": "C:/p", "lang": "de", "enable_flip_anim": False}


def test_tracked_config_uses_generic_prefix(toolkit_root):
    import os

    with open(os.path.join(toolkit_root, "config.json"), encoding="utf-8") as f:
        assert json.load(f)["prefix"] == "$$$/Plugin"


def test_default_plugin_path_is_empty():
    assert ltk.DEFAULT_CONFIG["plugin_path"] == ""
