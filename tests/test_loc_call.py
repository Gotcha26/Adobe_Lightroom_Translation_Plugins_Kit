"""Tests de la construction unifiée de l'appel LOC (#12)."""

import os

from tools.applicator.main import build_loc_call as applicator_build, process_plugin_directory
from tools.extractor.main import run_extraction
from tools.extractor.utils import build_loc_call


def test_leading_and_trailing_spaces():
    result = build_loc_call("$$$/K", "V", leading_spaces=1, trailing_spaces=1)
    assert result == '" " .. LOC "$$$/K=V" .. " "'


def test_suffix():
    assert build_loc_call("$$$/K", "V", suffix=" - ") == 'LOC "$$$/K=V" .. " - "'


def test_suffix_wins_over_trailing():
    result = build_loc_call("$$$/K", "V", trailing_spaces=2, suffix="...")
    assert result == 'LOC "$$$/K=V" .. "..."'


def test_plain():
    assert build_loc_call("$$$/K", "V") == 'LOC "$$$/K=V"'


def test_never_contains_underscore_call():
    for kwargs in ({"leading_spaces": 2}, {"trailing_spaces": 3}, {"suffix": " - "}, {}):
        assert "_(" not in build_loc_call("$$$/K", "V", **kwargs)


def test_applicator_delegates():
    member = {"loc_key": "$$$/K", "base_text": "V", "leading_spaces": 1, "trailing_spaces": 1, "suffix": ""}
    assert applicator_build(member) == '" " .. LOC "$$$/K=V" .. " "'


def test_integration_no_underscore_in_lua(plugin_dir, isolated_config):
    run_extraction(plugin_dir, "", "$$$/Test", "en", [], 3, False, silent=True)
    process_plugin_directory(plugin_dir, dry_run=False, create_backup=False, silent=True)
    with open(os.path.join(plugin_dir, "PWExport.lua"), encoding="utf-8") as f:
        content = f.read()
    assert 'LOC "' in content
    for line in content.splitlines():
        assert '_("' not in line, line
