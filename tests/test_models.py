"""Non-régression du modèle ExtractedString (#16) : suffixe par défaut vide."""

from tools.extractor.models import ExtractedString


def test_extracted_string_has_no_suffix_by_default():
    entry = ExtractedString(
        original_text="Export",
        clean_text="Export",
        base_text="Export",
        file_path="PWExport.lua",
        file_name="PWExport.lua",
        line_num=1,
        line_content='title = "Export"',
        pattern_name="title",
        suggested_key="$$$/Test/Export=Export",
    )
    assert entry.suffix == ""
    assert entry.has_suffix() is False
