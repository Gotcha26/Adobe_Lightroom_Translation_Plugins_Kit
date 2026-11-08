"""Non-régression ADD LANGUAGE (#13) : les helpers de config_loader doivent être importés."""

from tools.translator.addlang import validate_language_code


def test_validate_language_code(isolated_config):
    assert validate_language_code("de") == (True, "de", None)
    # La langue de référence ("en") est refusée
    assert validate_language_code("en")[0] is False
