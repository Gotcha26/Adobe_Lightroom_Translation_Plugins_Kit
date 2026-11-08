"""L'Extractor (menu et CLI) suit le préfixe configuré (#27)."""

from tools.extractor import main as extractor_main
from tools.extractor.menu import InteractiveMenu


def test_menu_uses_configured_prefix(isolated_config):
    assert InteractiveMenu("").prefix == "$$$/Test"


def test_cli_parser_default_prefix_is_configured(isolated_config):
    parser = extractor_main._build_parser()
    assert parser.parse_args([]).prefix == "$$$/Test"


def test_output_reuses_translator_warning_note():
    from tools.extractor import output
    from tools.translator import common

    assert output.TRANSLATION_WARNING_NOTE is common.TRANSLATION_WARNING_NOTE
