"""Tests des limites de l'Extractor relevées après #32/#22/#12 (#34).

Instructions multiples (log + libellé UI), ligne de fermeture d'un commentaire
bloc, échappements non simples, affichage du rapport, recherche ancrée.
"""

import glob
import os

import pytest

from tools.applicator.main import process_plugin_directory
from tools.extractor.engine import LocalizableStringExtractor
from tools.extractor.main import run_extraction
from tools.extractor.utils import VERBATIM_BACKSLASH, escape_lua_string, unescape_lua_string


def _plugin_with(tmp_path, source: str) -> str:
    plugin = tmp_path / "p.lrplugin"
    plugin.mkdir()
    (plugin / "PWExport.lua").write_text(source, encoding="utf-8")
    return str(plugin)


def _extract(plugin_dir):
    extractor = LocalizableStringExtractor(plugin_dir, prefix="$$$/Test")
    extractor.extract_all()
    return extractor


def _run_pipeline(plugin_dir) -> str:
    """Extraction puis application ; renvoie le PWExport.lua obtenu."""
    run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, True, silent=True)
    process_plugin_directory(plugin_dir, dry_run=False, create_backup=False, silent=True)
    with open(os.path.join(plugin_dir, "PWExport.lua"), encoding="utf-8") as f:
        return f.read()


def _extraction_file(plugin_dir, name) -> str:
    files = glob.glob(os.path.join(plugin_dir, "__i18n_tmp__", "*Extractor", "*", name))
    assert len(files) == 1, files
    with open(files[0], encoding="utf-8") as f:
        return f.read()


def _read_translated_strings(plugin_dir) -> str:
    return _extraction_file(plugin_dir, "TranslatedStrings_en.txt")


# --- Point 3 : échappements non simples ---------------------------------------

@pytest.mark.parametrize("source, real", [
    # Octets UTF-8 en décimal (\ddd), forme courante en Lua 5.1 : « é »
    ("Caf\\195\\169", "Café"),
    ("Caf\\xC3\\xA9", "Café"),
    # Suite d'octets en UTF-8 invalide : conservée telle quelle, son \ marqué
    # par VERBATIM_BACKSLASH pour ne pas être doublé au ré-échappement
    ("Caf\\xc3\\251x", "Caf" + VERBATIM_BACKSLASH + "xc3" + VERBATIM_BACKSLASH + "251x"),
    ("Skip \\z  x", "Skip " + VERBATIM_BACKSLASH + "z  x"),
    ("\\65BC", "ABC"),
    ("\\u{E9}t\\u{E9}", "été"),
    ("A\\0B", "A\x00B"),
])
def test_unescape_decodes_numeric_escapes(source, real):
    assert unescape_lua_string(source) == real


@pytest.mark.parametrize("source, back", [
    # Séquences décodées : ressortent sous une forme de même valeur Lua
    ("Caf\\195\\169", "Café"),
    ("Caf\\xC3\\xA9", "Café"),
    ("Code \\u{48}", "Code H"),
    ("NUL \\0 then 1\\0001", "NUL \\000 then 1\\0001"),
    ('Mixed \\"q\\" \\\\ \\n \\t \\195\\169', 'Mixed \\"q\\" \\\\ \\n \\t é'),
])
def test_unescape_escape_roundtrip_preserves_lua_value(source, back):
    assert escape_lua_string(unescape_lua_string(source)) == back
    assert unescape_lua_string(back) == unescape_lua_string(source)


@pytest.mark.parametrize("source", [
    "Bad \\200 byte", "\\xff\\xfe", "Skip \\z   spaces", "Bad \\q escape",
    "Too big \\300", "Big \\u{7FFFFFFF}", "Code \\u{D800}",
])
def test_undecoded_sequences_come_back_verbatim(source):
    """Une séquence non décodée ressort identique (\\ jamais doublé devant elle)."""
    assert escape_lua_string(unescape_lua_string(source)) == source


def test_real_backslash_is_still_doubled():
    # Texte réel « C:\200 » (barre oblique réelle) : jamais confondu avec \200
    assert escape_lua_string("C:\\200") == "C:\\\\200"
    assert unescape_lua_string("C:\\\\200") == "C:\\200"


def test_decoded_utf8_string_is_extracted_as_real_text(tmp_path):
    plugin = _plugin_with(tmp_path, 'local t = { title = "Caf\\195\\169 ouvert" }\n')
    entries = _extract(plugin).extracted
    assert [e.base_text for e in entries] == ["Café ouvert"]
    assert entries[0].original_text == "Caf\\195\\169 ouvert"


def test_decimal_escapes_end_to_end(tmp_path, isolated_config):
    plugin = _plugin_with(tmp_path, 'local t = { title = "Caf\\195\\169 ouvert" }\n'
                                    'local u = { title = "Bad \\200 byte here" }\n')
    lua = _run_pipeline(plugin)
    assert 'title = LOC "$$$/Test/PWExport/CafOuvert=Café ouvert"' in lua
    assert 'title = "Bad \\200 byte here"' in lua
    strings = _read_translated_strings(plugin)
    assert '"$$$/Test/PWExport/CafOuvert=Café ouvert"' in strings
    assert "Bad" not in strings


def test_undecodable_string_is_not_extracted(tmp_path):
    # Octet isolé (UTF-8 invalide) : pas représentable dans un fichier texte UTF-8
    plugin = _plugin_with(tmp_path, 'local t = { title = "Bad \\200 byte here" }\n')
    extractor = _extract(plugin)
    assert extractor.extracted == []
    assert extractor.stats.technical_ignored == 1
