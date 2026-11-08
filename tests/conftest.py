"""Fixtures partagées des tests du toolkit."""

import json
import os
import shutil

import pytest

TOOLKIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_PLUGIN = os.path.join(TOOLKIT_ROOT, "tests", "fixtures", "plugin.lrplugin")


@pytest.fixture(autouse=True)
def _french_ui_language():
    """Fige la langue d'interface sur le français (langue source) pour chaque test.

    Les assertions portent sur des libellés français ; sans cela, le résultat
    dépendrait de la langue du poste ou du runner CI.
    """
    from core import i18n

    previous = i18n.get_current_language()
    i18n.set_language("fr")
    yield
    i18n.set_language(previous)


@pytest.fixture
def toolkit_root() -> str:
    """Racine du dépôt."""
    return TOOLKIT_ROOT


@pytest.fixture
def plugin_dir(tmp_path) -> str:
    """Copie du plugin de test dans un dossier temporaire ; renvoie son chemin."""
    dest = tmp_path / "plugin.lrplugin"
    shutil.copytree(FIXTURE_PLUGIN, dest)
    return str(dest)


@pytest.fixture
def isolated_config(monkeypatch, tmp_path) -> str:
    """Isole la configuration : aucun test ne lit ni n'écrit la vraie config.

    Renvoie le dossier temporaire contenant un config.json minimal.
    """
    import LocalizationToolKit
    from tools.translator import config_loader

    config_dir = tmp_path / "config_root"
    config_dir.mkdir()
    minimal = {"lang": "en", "prefix": "$$$/Test", "temp_dir": "__i18n_tmp__"}
    (config_dir / "config.json").write_text(json.dumps(minimal), encoding="utf-8")
    config_dir_str = str(config_dir)

    monkeypatch.setattr(config_loader, "_get_root_dir", lambda: config_dir_str)

    original_init = LocalizationToolKit.ConfigManager.__init__

    def patched_init(self, base_dir=None):
        original_init(self, config_dir_str)

    monkeypatch.setattr(LocalizationToolKit.ConfigManager, "__init__", patched_init)
    return config_dir_str
