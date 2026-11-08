"""COMPARE doit nommer ses sorties d'après la langue de référence configurée (#19)."""

import json
import os

from tools.translator.common import load_update_json
from tools.translator.compare import run_compare


def test_compare_uses_configured_reference_lang(isolated_config, plugin_dir, tmp_path):
    with open(os.path.join(isolated_config, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"lang": "fr", "prefix": "$$$/Test", "temp_dir": "__i18n_tmp__"}, f)

    old = os.path.join(plugin_dir, "TranslatedStrings_en.txt")
    new = os.path.join(plugin_dir, "TranslatedStrings_fr.txt")
    out = str(tmp_path / "out")

    run_compare(old, new, out)

    names = set(os.listdir(out))
    assert "UPDATE_fr.json" in names
    assert "TranslatedStrings_fr.txt" in names
    assert "old_TranslatedStrings_fr.txt" in names
    assert "UPDATE_en.json" not in names
    assert "TranslatedStrings_en.txt" not in names
    assert load_update_json(out) is not None
