"""Tests de l'analyse Lua de l'Extractor : guillemets échappés et commentaires bloc (#22)."""

import glob
import os

from tools.applicator.main import apply_replacements_to_line, process_plugin_directory
from tools.extractor.engine import LocalizableStringExtractor
from tools.extractor.main import run_extraction
from tools.extractor.utils import (
    block_comment_state, build_loc_call, extract_all_string_literals, unescape_lua_string
)


def _extract(plugin_dir):
    extractor = LocalizableStringExtractor(plugin_dir, prefix="$$$/Test")
    extractor.extract_all()
    return extractor


def _export_entries(extractor):
    return [e for e in extractor.extracted if e.file_name == "PWExport.lua"]


# --- Littéraux avec échappements ---------------------------------------------

def test_literal_with_escaped_quotes_is_captured_whole():
    line = 'LrDialogs.message("Cannot open \\"file\\"", "Check the path")'
    texts = [t for t, _s, _e in extract_all_string_literals(line)]
    assert texts == ['Cannot open \\"file\\"', "Check the path"]


def test_literal_with_escaped_quote_then_concatenation():
    line = 'LrDialogs.message("Cannot open \\"" .. name .. "\\"", "Check the path")'
    texts = [t for t, _s, _e in extract_all_string_literals(line)]
    assert texts == ['Cannot open \\"', '\\"', "Check the path"]


def test_literal_with_escaped_backslash():
    line = 'x = "C:\\\\dir\\\\" .. y'
    texts = [t for t, _s, _e in extract_all_string_literals(line)]
    assert texts == ["C:\\\\dir\\\\"]


def test_unescape_lua_string():
    assert unescape_lua_string('Cannot open \\"file\\"') == 'Cannot open "file"'
    assert unescape_lua_string("C:\\\\dir") == "C:\\dir"
    assert unescape_lua_string("plain") == "plain"


def test_build_loc_call_escapes_quotes_and_backslashes():
    assert build_loc_call("$$$/K", 'Say "hi"') == 'LOC "$$$/K=Say \\"hi\\""'
    assert build_loc_call("$$$/K", "C:\\dir") == 'LOC "$$$/K=C:\\\\dir"'
    assert build_loc_call("$$$/K", "V", suffix='"') == 'LOC "$$$/K=V" .. "\\""'


def test_block_comment_state():
    assert block_comment_state("--[[ title = \"x\" ]]", None) is None
    assert block_comment_state("--[[", None) == ""
    assert block_comment_state("--[==[ start", None) == "=="
    assert block_comment_state("still ]] inside", "==") == "=="
    assert block_comment_state("]==] x = 1", "==") is None
    assert block_comment_state('x = f() --[[ trailing opener', None) == ""
    assert block_comment_state("-- line comment --[[", None) is None
    assert block_comment_state('x = "--[[ not a comment"', None) is None


# --- Extraction sur la fixture -----------------------------------------------

def test_escaped_string_extracted_as_single_key(plugin_dir):
    entries = _export_entries(_extract(plugin_dir))
    quoted = [e for e in entries if "Cannot open" in e.original_text]
    assert len(quoted) == 1
    entry = quoted[0]
    assert entry.original_text == 'Cannot open \\"file\\"'
    assert entry.base_text == 'Cannot open "file"'
    assert entry.suggested_key == "$$$/Test/Export/CannotOpenFile"
    assert not any(e.base_text.endswith("\\") for e in entries)


def test_block_comment_is_ignored(plugin_dir):
    entries = _export_entries(_extract(plugin_dir))
    assert not any("Old label" in e.original_text for e in entries)


def test_multiline_block_comment_is_ignored(plugin_dir):
    path = os.path.join(plugin_dir, "PWExport.lua")
    with open(path, "a", encoding="utf-8") as f:
        f.write('\n--[==[\n  title = "Commented ]] still comment"\n]==]\nlocal t = { title = "After comment" }\n')
    entries = _export_entries(_extract(plugin_dir))
    texts = [e.base_text for e in entries]
    assert not any("Commented" in t for t in texts)
    assert "After comment" in texts


def test_existing_loc_with_escaped_quotes(plugin_dir):
    path = os.path.join(plugin_dir, "PWExport.lua")
    with open(path, "a", encoding="utf-8") as f:
        f.write('\nlocal q = { title = LOC "$$$/Test/Export/Quoted=Say \\"hi\\"" }\n')
    entries = _export_entries(_extract(plugin_dir))
    existing = [e for e in entries if e.suggested_key == "$$$/Test/Export/Quoted"]
    assert existing
    assert {e.base_text for e in existing} == {'Say "hi"'}
    assert {e.original_text for e in existing} == {'Say \\"hi\\"'}


# --- Chaîne complète Extractor -> TranslatedStrings / Applicator ------------

def test_translated_strings_value_is_escaped(plugin_dir, isolated_config, tmp_path):
    out = tmp_path / "out"
    run_extraction(plugin_dir, str(out), "$$$/Test", "en", [], 3, True, silent=True)
    files = glob.glob(os.path.join(str(out), "*", "TranslatedStrings_en.txt"))
    assert len(files) == 1
    with open(files[0], encoding="utf-8") as f:
        content = f.read()
    assert '"$$$/Test/Export/CannotOpenFile=Cannot open \\"file\\""' in content
    assert "Old label" not in content


def test_applicator_writes_escaped_loc_call(plugin_dir, isolated_config):
    run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, True, silent=True)
    process_plugin_directory(plugin_dir, dry_run=False, create_backup=False, silent=True)
    with open(os.path.join(plugin_dir, "PWExport.lua"), encoding="utf-8") as f:
        content = f.read()
    assert 'LOC "$$$/Test/Export/CannotOpenFile=Cannot open \\"file\\""' in content
    assert '--[[ title = "Old label" ]]' in content


def test_apply_replacements_to_line_with_escaped_member():
    line = 'LrDialogs.message("Cannot open \\"file\\"", "x")'
    member = {"original_text": 'Cannot open \\"file\\"', "base_text": 'Cannot open "file"',
              "loc_key": "$$$/Test/Export/CannotOpenFile"}
    result, applied = apply_replacements_to_line(line, [member])
    assert applied == [member]
    assert result == 'LrDialogs.message(LOC "$$$/Test/Export/CannotOpenFile=Cannot open \\"file\\"", "x")'
