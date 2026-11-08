"""Tests de ConfigManager : séparation config.json / config.local.json (#18)."""

import json
from pathlib import Path

import pytest

import LocalizationToolKit as ltk
from LocalizationToolKit import ConfigManager
from core.colors import c
from core.i18n import _


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


def test_set_reports_whether_value_was_saved(tmp_path):
    cm = ConfigManager(str(tmp_path))
    assert cm.set("enable_flip_anim", False) is True

    (tmp_path / "config.local.json").write_bytes(b"{")
    cm = ConfigManager(str(tmp_path))
    assert cm.set("enable_flip_anim", True) is False


def test_set_reports_failed_save(tmp_path):
    cm = ConfigManager(str(tmp_path))
    cm.config_local_path = str(tmp_path / "missing_dir" / "config.local.json")
    assert cm.set("enable_flip_anim", False) is False
    assert cm.get("enable_flip_anim") is False  # appliqué en mémoire


def _menu_with_unreadable_local(isolated_config, monkeypatch, answers):
    """MainMenu dont le config.local.json est illisible (JSON tronqué)."""
    (Path(isolated_config) / "config.local.json").write_bytes(b"{")
    menu = ltk.MainMenu()
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(ltk, "set_i18n_dir", lambda name: None)  # pas d'état global modifié
    feed = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *_a: next(feed, ""))
    return menu


def _session_only(message: str) -> str:
    return c.warning(_("{message} (pour cette session uniquement)").format(message=message))


def test_plugin_path_unsaved_is_reported_as_session_only(isolated_config, monkeypatch, capsys, tmp_path):
    plugin = tmp_path / "p.lrplugin"
    plugin.mkdir()
    menu = _menu_with_unreadable_local(isolated_config, monkeypatch, [str(plugin)])
    menu.input_plugin_path()
    out = capsys.readouterr().out
    message = _("Plugin configuré: {path}").format(path=str(plugin))
    assert c.success(message) not in out
    assert _session_only(message) in out
    assert menu.config.get("plugin_path") == str(plugin)


def test_temp_dir_unsaved_is_reported_as_session_only(isolated_config, monkeypatch, capsys):
    menu = _menu_with_unreadable_local(isolated_config, monkeypatch, ["__other_tmp__"])
    menu.input_temp_dir()
    out = capsys.readouterr().out
    message = _("Dossier temporaire: {name}").format(name="__other_tmp__")
    assert c.success(message) not in out
    assert _session_only(message) in out


@pytest.mark.parametrize("choice, answers, message", [
    ("3", [], lambda: _("Auto-ajout au .gitignore: {status}").format(status=_("désactivé"))),
    ("4", [], lambda: _("Animation au démarrage: {status}").format(status=_("désactivée"))),
    ("5", ["$$$/New"], lambda: _("Préfixe: {prefix}").format(prefix="$$$/New")),
    ("6", ["de"], lambda: _("Langue: {lang}").format(lang="de")),
    ("7", [], lambda: _("Debug i18n: {status}").format(status=_("activé"))),
])
def test_configuration_unsaved_is_reported_as_session_only(isolated_config, monkeypatch, capsys,
                                                           choice, answers, message):
    menu = _menu_with_unreadable_local(isolated_config, monkeypatch, [choice, *answers, ""])
    menu.configure_paths()
    out = capsys.readouterr().out
    assert c.success(message()) not in out
    assert _session_only(message()) in out


def test_configuration_saved_is_reported_as_success(isolated_config, monkeypatch, capsys):
    menu = ltk.MainMenu()
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    feed = iter(["6", "de", ""])
    monkeypatch.setattr("builtins.input", lambda *_a: next(feed, ""))
    menu.configure_paths()
    assert c.success(_("Langue: {lang}").format(lang="de")) in capsys.readouterr().out


def test_tracked_config_uses_generic_prefix(toolkit_root):
    import os

    with open(os.path.join(toolkit_root, "config.json"), encoding="utf-8") as f:
        assert json.load(f)["prefix"] == "$$$/Plugin"


def test_default_plugin_path_is_empty():
    assert ltk.DEFAULT_CONFIG["plugin_path"] == ""
