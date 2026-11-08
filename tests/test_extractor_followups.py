"""Tests des limites de l'Extractor relevées après #32/#22/#12 (#34).

Instructions multiples (log + libellé UI), ligne de fermeture d'un commentaire
bloc, échappements non simples, affichage du rapport, recherche ancrée.
"""

import glob
import os

import pytest

from tools.applicator.main import apply_replacements_to_line, process_plugin_directory
from tools.extractor.engine import LocalizableStringExtractor, MultiLineContext
from tools.extractor.main import run_extraction
from tools.extractor.models import ExtractedString
from tools.extractor.output import OutputGenerator
from tools.extractor.utils import (
    VERBATIM_BACKSLASH, escape_lua_string, find_literal_positions, log_call_spans,
    unescape_lua_string
)


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


# --- Point 5 : recherche ancrée sur des littéraux entiers ----------------------

# "Open \"Export\"" se termine par \"Export\"" : un find brut de "Export\""
# (membre `Export\"`, texte réel « Export" ») tombe au milieu de ce littéral.
_TAIL_LINE = 'local t = { title = "Open \\"Export\\"", tooltip = "Export\\"" }'
_TAIL_MEMBER = {"original_text": 'Export\\"', "base_text": 'Export"', "loc_key": "$$$/T/E"}


def test_find_literal_positions_is_anchored():
    assert find_literal_positions(_TAIL_LINE, 'Export\\"') == [_TAIL_LINE.index('"Export\\"" }')]
    # Entre la fin d'un littéral et le début du suivant : pas un littéral
    assert find_literal_positions('t = {"a", "b"}', ', ') == []
    assert find_literal_positions('t = {"a", ", "}', ', ') == [10]
    # Un littéral entre apostrophes n'est pas une chaîne entre guillemets doubles
    assert find_literal_positions("s = '\"Export\"'", "Export") == []


def test_applicator_replaces_whole_literal_only():
    result, applied = apply_replacements_to_line(_TAIL_LINE, [_TAIL_MEMBER])
    assert applied == [_TAIL_MEMBER]
    assert result == 'local t = { title = "Open \\"Export\\"", tooltip = LOC "$$$/T/E=Export\\"" }'


def test_applicator_ignores_gap_between_literals():
    member = {"original_text": ", ", "base_text": ", ", "loc_key": "$$$/T/C"}
    result, applied = apply_replacements_to_line('t = {"a", "b"}', [member])
    assert (result, applied) == ('t = {"a", "b"}', [])


def test_build_replaced_line_is_anchored():
    # Littéral visé en premier : un rfind brut tomberait dans le second littéral
    line = 'local t = { tooltip = "Export\\"", title = "Open \\"Export\\"" }'
    entry = ExtractedString(
        original_text='Export\\"', clean_text='Export"', base_text='Export"',
        file_path="PWExport.lua", file_name="PWExport.lua", line_num=1,
        line_content=line, pattern_name="tooltip", suggested_key="$$$/T/E")
    replaced = OutputGenerator("", "$$$/T", silent=True)._build_replaced_line(line, [entry])
    assert replaced == 'local t = { tooltip = LOC "$$$/T/E=Export\\"", title = "Open \\"Export\\"" }'


def test_multiline_find_line_for_string_is_anchored():
    ctx = MultiLineContext()
    ctx.start("LrDialogs.message", 10, 'LrDialogs.message("Open \\"Export\\"",')
    ctx.add_line(11, '  "Export\\"")')
    assert ctx.find_line_for_string('Export\\"') == 11


def test_anchored_search_end_to_end(tmp_path, isolated_config):
    plugin = _plugin_with(tmp_path, _TAIL_LINE + "\n")
    lua = _run_pipeline(plugin)
    assert lua == ('local t = { title = LOC "$$$/Test/PWExport/OpenExport=Open \\"Export\\"", '
                   'tooltip = LOC "$$$/Test/PWExport/Export=Export\\"" }\n')


# --- Point 1 : appel de log + libellé UI sur la même ligne ----------------------

def test_log_call_spans():
    line = 'log:info("Starting export"); title = "Export file"'
    assert log_call_spans(line) == [(8, line.index(";"))]
    assert log_call_spans('logInfo("a", f("b")) x = "c"') == [(7, 20)]
    # Appel sans parenthèses (sucre Lua) : seul le littéral est l'argument
    line = 'log:trace "Some message"; title = "Shown"'
    assert log_call_spans(line) == [(10, 24)]
    # « log( » à l'intérieur d'une chaîne n'est pas un appel de log
    assert log_call_spans('title = "See log(s) here"') == []
    # Appel non fermé sur la ligne : jusqu'à la fin de la ligne
    assert log_call_spans('log("a", "b"') == [(3, 12)]


def test_log_and_ui_literal_on_same_line(tmp_path, isolated_config):
    plugin = _plugin_with(tmp_path, 'log:info("Starting export"); title = "Export file"\n')
    extractor = _extract(plugin)
    assert [e.base_text for e in extractor.extracted] == ["Export file"]
    assert extractor.stats.log_lines_ignored == 1
    lua = _run_pipeline(plugin)
    assert lua == 'log:info("Starting export"); title = LOC "$$$/Test/PWExport/ExportFile=Export file"\n'


def test_log_and_ui_literal_with_same_text(tmp_path, isolated_config):
    # Même texte dans le log et dans l'UI : seul le littéral de l'UI est remplacé
    plugin = _plugin_with(tmp_path, '  logInfo("Export file"); local t = { title = "Export file" }\n')
    lua = _run_pipeline(plugin)
    assert lua == ('  logInfo("Export file"); '
                   'local t = { title = LOC "$$$/Test/PWExport/ExportFile=Export file" }\n')


def test_log_call_sugar_and_ui_literal(tmp_path):
    plugin = _plugin_with(tmp_path, 'log:trace "Some message"; title = "Shown title"\n')
    assert [e.base_text for e in _extract(plugin).extracted] == ["Shown title"]


def test_log_only_line_extracts_nothing(tmp_path):
    plugin = _plugin_with(tmp_path, 'logInfo("Saving title = now")\n')
    assert _extract(plugin).extracted == []


def test_log_word_inside_string_is_not_a_log_call(tmp_path):
    plugin = _plugin_with(tmp_path, 'local t = { title = "See log(s) here" }\n')
    extractor = _extract(plugin)
    assert [e.base_text for e in extractor.extracted] == ["See log(s) here"]
    assert extractor.stats.log_lines_ignored == 0


def test_log_literals_skipped_in_multiline_block(tmp_path):
    plugin = _plugin_with(tmp_path, 'LrDialogs.message("Upload failed",\n'
                                    '  "Check the server"); log:warn("Upload failed badly")\n')
    texts = [e.base_text for e in _extract(plugin).extracted]
    assert texts == ["Upload failed", "Check the server"]
