"""Tests de la mise à jour chirurgicale des TranslatedStrings (#20)."""

import os

from tools.translator.common import (
    TRANSLATION_WARNING_NOTE,
    parse_translation_file,
    update_translation_file_surgical,
)


def _fr_file(plugin_dir: str) -> str:
    return os.path.join(plugin_dir, "TranslatedStrings_fr.txt")


def _read_lines(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def test_round_trip_is_idempotent_and_handles_escaped_quotes(plugin_dir, isolated_config):
    target = _fr_file(plugin_dir)
    original = parse_translation_file(target)

    # Aller-retour avec des traductions identiques : rien ne change
    def _without_generated(lines):
        return [line for line in lines if not line.startswith("-- Generated:")]

    before = _read_lines(target)
    update_translation_file_surgical(target, None, dict(original))
    first_pass = _read_lines(target)
    update_translation_file_surgical(target, None, dict(original))
    assert parse_translation_file(target) == original
    assert _without_generated(first_pass) == _without_generated(before)
    assert _without_generated(_read_lines(target)) == _without_generated(first_pass)

    # Une nouvelle valeur contenant des guillemets échappés doit être écrite
    translations = dict(original)
    translations["$$$/Test/Export/Quoted"] = 'Say \\"hi\\"'
    update_translation_file_surgical(target, None, translations)

    assert parse_translation_file(target) == translations
    assert '"$$$/Test/Export/Quoted=Say \\"hi\\""' in _read_lines(target)


def test_remove_unlisted_drops_extra_keys(plugin_dir, isolated_config):
    target = _fr_file(plugin_dir)
    translations = parse_translation_file(target)
    del translations["$$$/Test/Export/Old"]

    update_translation_file_surgical(target, None, translations, remove_unlisted=True)

    result = parse_translation_file(target)
    assert "$$$/Test/Export/Old" not in result
    assert result == translations


def test_remove_unlisted_also_adds_missing_keys(plugin_dir, isolated_config):
    """Sans UPDATE, SYNC annonce des clés ajoutées : elles doivent être écrites."""
    target = _fr_file(plugin_dir)
    translations = parse_translation_file(target)
    translations["$$$/Test/Export/Missing"] = "Manquante"

    update_translation_file_surgical(target, None, translations, remove_unlisted=True)

    assert parse_translation_file(target) == translations
    assert _read_lines(target).count("-- Export") == 1


def test_markers_are_replaced_not_stacked(plugin_dir, isolated_config):
    target = _fr_file(plugin_dir)
    translations = parse_translation_file(target)
    translations["$$$/Test/Export/New"] = "Nouveau"
    review = "-- [NEEDS_REVIEW] Reference text was modified"
    new = "-- [NEW] To translate"
    markers = {"$$$/Test/Export/Existing": review, "$$$/Test/Export/New": new}
    update_data = {"added": {"$$$/Test/Export/New": "New"}, "changed": {"$$$/Test/Export/Existing": {}}}

    for _pass in range(2):
        update_translation_file_surgical(target, update_data, translations, markers, remove_unlisted=True)

    lines = _read_lines(target)
    assert lines.count(review) == 1
    assert lines.count(new) == 1
    assert lines[lines.index(review) + 1].startswith('"$$$/Test/Export/Existing=')
    assert lines[lines.index(new) + 1] == '"$$$/Test/Export/New=Nouveau"'


def test_added_key_goes_into_its_existing_section(plugin_dir, isolated_config):
    target = _fr_file(plugin_dir)
    translations = parse_translation_file(target)
    new_key = "$$$/Test/Export/New"
    translations[new_key] = "Nouveau"
    update_data = {"added": {new_key: "New"}, "deleted": [], "changed": {}}

    update_translation_file_surgical(target, update_data, translations)

    lines = _read_lines(target)
    new_line = f'"{new_key}=Nouveau"'
    assert lines.count("-- Export") == 1
    assert new_line in lines
    # Insérée juste après la dernière clé de la section Export, pas en fin de fichier
    quoted_index = next(i for i, line in enumerate(lines) if line.startswith('"$$$/Test/Export/Quoted='))
    assert lines.index(new_line) == quoted_index + 1
    assert lines.index(new_line) > lines.index("-- Export")


def test_header_updated_with_translator_note_present(plugin_dir, isolated_config):
    target = _fr_file(plugin_dir)
    translations = parse_translation_file(target)
    translations["$$$/Test/Export/New"] = "Nouveau"
    update_data = {"added": {"$$$/Test/Export/New": "New"}}
    metadata = {"total_keys": 4, "new_keys": 1, "source": "SYNC"}

    update_translation_file_surgical(target, update_data, translations, metadata=metadata)

    lines = _read_lines(target)
    closing = [i for i, line in enumerate(lines) if line.startswith("-- ====")][1]
    header = lines[:closing]
    assert "-- Total keys: 4" in header
    assert "-- New keys: 1" in header
    assert "-- Source: SYNC" in header
    # La note aux traducteurs est recopiée telle quelle
    note_lines = TRANSLATION_WARNING_NOTE.rstrip("\n").splitlines()
    start = lines.index(note_lines[0], closing)
    assert lines[start:start + len(note_lines)] == note_lines
    # Aucune clé insérée dans la note ni de fausse section créée
    assert lines.count("-- Export") == 1
    assert all(lines.count(note_line) == 1 for note_line in note_lines if note_line.startswith("-- 1"))
