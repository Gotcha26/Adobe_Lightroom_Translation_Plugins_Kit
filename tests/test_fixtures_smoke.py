"""Vérifie que les fixtures du socle de tests fonctionnent."""

import os


def test_plugin_dir_is_copy(plugin_dir):
    assert os.path.isfile(os.path.join(plugin_dir, "PWExport.lua"))
    assert os.path.isfile(os.path.join(plugin_dir, "ui", "Dialog.lua"))
    assert os.path.isfile(os.path.join(plugin_dir, "api", "Dialog.lua"))
    assert os.path.isfile(os.path.join(plugin_dir, "TranslatedStrings_fr.txt"))


def test_isolated_config(isolated_config):
    from tools.translator import config_loader

    assert config_loader._get_root_dir() == isolated_config
