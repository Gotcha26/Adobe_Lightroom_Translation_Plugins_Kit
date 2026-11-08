"""Le format TRANSLATE_xx.txt doit être stable, non traduisible et suivre la langue de référence (#21)."""

import json
import os

from core.i18n import temporary_language
from tools.translator.common import load_update_json
from tools.translator.compare import run_compare
from tools.translator.extract import run_extract
from tools.translator.inject import parse_translate_file


def _build_update(plugin_dir, tmp_path):
    """Produit un UPDATE json avec une clé ajoutée et une clé modifiée."""
    old = os.path.join(plugin_dir, "TranslatedStrings_en.txt")
    with open(old, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.splitlines()
    key_lines = [i for i, ln in enumerate(lines) if ln.startswith('"$$$/')]
    assert key_lines, "fixture sans clés"
    first = lines[key_lines[0]]
    k, v = first.strip().strip('"').split("=", 1)
    changed_key = k
    lines[key_lines[0]] = f'"{k}={v} MODIFIED"'
    lines.insert(key_lines[0] + 1, '"$$$/Test/Added=Brand new value"')
    new = str(tmp_path / "new_en.txt")
    with open(new, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    out = str(tmp_path / "out")
    run_compare(old, new, out)
    data = load_update_json(out)
    assert data["added"] and data["changed"]
    return out, data, changed_key


def _check(out, data, lang, tmp_path):
    with temporary_language("en"):
        path = run_extract(out, lang, None, str(tmp_path / "tr"))
        result = parse_translate_file(path, None)
    for key, value in data["added"].items():
        assert result[key] == value
    for key, change in data["changed"].items():
        assert result[key] == change["new"]


def test_roundtrip_under_english_ui(isolated_config, plugin_dir, tmp_path):
    out, data, _k = _build_update(plugin_dir, tmp_path)
    _check(out, data, "fr", tmp_path)


def test_roundtrip_with_fr_reference(isolated_config, plugin_dir, tmp_path):
    with open(os.path.join(isolated_config, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"lang": "fr", "prefix": "$$$/Test", "temp_dir": "__i18n_tmp__"}, f)
    out, data, _k = _build_update(plugin_dir, tmp_path)
    _check(out, data, "de", tmp_path)


def test_legacy_markers_still_read(tmp_path):
    p = tmp_path / "TRANSLATE_fr.txt"
    p.write_text(
        "[KEY] $$$/A/b\n[EN AVANT]  old\n[EN APRÈS]  new value\n[FR] → \n\n"
        "[KEY] $$$/A/c\n[EN]  plain\n[FR] → \n",
        encoding="utf-8",
    )
    result = parse_translate_file(str(p), None)
    assert result["$$$/A/b"] == "new value"
    assert result["$$$/A/c"] == "plain"


def test_raw_quotes_in_translation_are_escaped(isolated_config, tmp_path):
    """#21 #22 : un « " » saisi brut est échappé, sinon la ligne ne se relit plus."""
    from tools.translator.common import parse_translation_file
    from tools.translator.inject import run_inject

    p = tmp_path / "TRANSLATE_fr.txt"
    p.write_text(
        "[KEY] $$$/Test/Open\n[EN]  Cannot open \\\"file\\\"\n"
        "[FR] → Impossible d'ouvrir \"fichier\"\n\n"
        "[KEY] $$$/Test/Kept\n[EN]  x\n[FR] → Déjà \\\"échappé\\\" et \\n saut\n",
        encoding="utf-8",
    )
    assert parse_translate_file(str(p), None)["$$$/Test/Open"] == "Impossible d'ouvrir \\\"fichier\\\""

    target = tmp_path / "TranslatedStrings_fr.txt"
    run_inject(str(p), str(target), update_dir=str(tmp_path), create_backup=False)

    parsed = parse_translation_file(str(target))
    assert parsed["$$$/Test/Open"] == "Impossible d'ouvrir \\\"fichier\\\""
    assert parsed["$$$/Test/Kept"] == "Déjà \\\"échappé\\\" et \\n saut"


def test_escape_translation_value():
    from tools.translator.common import escape_translation_value

    assert escape_translation_value('a "b"') == 'a \\"b\\"'
    assert escape_translation_value('a \\"b\\"') == 'a \\"b\\"'
    assert escape_translation_value('C:\\dossier') == 'C:\\\\dossier'
    assert escape_translation_value('x\\\\y \\n \\t') == 'x\\\\y \\n \\t'


def test_translate_header_explains_quote_escaping(isolated_config, plugin_dir, tmp_path):
    out, _data, _k = _build_update(plugin_dir, tmp_path)
    with temporary_language("fr"):
        path = run_extract(out, "fr", None, str(tmp_path / "tr"))
    with open(path, encoding="utf-8") as f:
        header = [ln for ln in f if ln.startswith("#")]
    assert any('\\"' in ln for ln in header), header
