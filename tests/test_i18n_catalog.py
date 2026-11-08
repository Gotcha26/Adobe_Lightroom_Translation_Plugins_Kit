"""Catalogue gettext EN : complet, cohérent avec le code, et réellement utilisé (#29)."""

import ast
import importlib.util
import os
import subprocess
import sys

PO_RELATIVE = os.path.join("locale", "en", "LC_MESSAGES", "messages.po")
SCANNED_PATHS = ("LocalizationToolKit.py", "core", "tools")


def _load_extractor(toolkit_root):
    """Charge tests/tools/extract_messages.py sans exiger de paquet tests."""
    path = os.path.join(toolkit_root, "tests", "tools", "extract_messages.py")
    spec = importlib.util.spec_from_file_location("extract_messages", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parse_po(path):
    """Analyse minimale d'un .po : liste de dicts {msgid, msgid_plural, msgstr: [..]}.

    Les entrées obsolètes (#~) et les commentaires sont ignorés.
    """
    entries = []
    current = None
    field = None

    def flush():
        if current is not None:
            entries.append(current)

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("msgid "):
                flush()
                current = {"msgid": "", "msgid_plural": None, "msgstr": {}}
                field = ("msgid", None)
                current["msgid"] = ast.literal_eval(line[len("msgid "):])
            elif line.startswith("msgid_plural "):
                field = ("msgid_plural", None)
                current["msgid_plural"] = ast.literal_eval(line[len("msgid_plural "):])
            elif line.startswith("msgstr["):
                index = int(line[len("msgstr["):line.index("]")])
                field = ("msgstr", index)
                current["msgstr"][index] = ast.literal_eval(line[line.index("]") + 2:])
            elif line.startswith("msgstr "):
                field = ("msgstr", 0)
                current["msgstr"][0] = ast.literal_eval(line[len("msgstr "):])
            elif line.startswith('"'):
                name, index = field
                value = ast.literal_eval(line)
                if name == "msgstr":
                    current["msgstr"][index] += value
                else:
                    current[name] += value
    flush()
    return entries


def test_po_has_no_empty_msgstr(toolkit_root):
    entries = _parse_po(os.path.join(toolkit_root, PO_RELATIVE))
    empty = [
        e["msgid"] for e in entries
        if e["msgid"] and any(not value for value in e["msgstr"].values())
    ]
    assert empty == [], "msgstr vides : {}".format(empty[:20])


def test_every_code_msgid_is_in_po(toolkit_root):
    extractor = _load_extractor(toolkit_root)
    code_ids = extractor.extract_messages(
        [os.path.join(toolkit_root, p) for p in SCANNED_PATHS]
    )
    entries = _parse_po(os.path.join(toolkit_root, PO_RELATIVE))
    po_ids = set()
    for e in entries:
        po_ids.add(e["msgid"])
        if e["msgid_plural"]:
            po_ids.add(e["msgid_plural"])
    missing = sorted(code_ids - po_ids)
    assert missing == [], "{} msgid absents du .po : {}".format(len(missing), missing[:20])


def test_error_prefix_is_translated_in_english(toolkit_root):
    env = dict(os.environ, TOOLKIT_LANG="en", PYTHONIOENCODING="utf-8")
    code = "from core.colors import c; print(c.error('x')); print(c.warning('y'))"
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=toolkit_root, env=env,
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    assert "[ERROR]" in result.stdout
    assert "[WARNING]" in result.stdout
    assert "ERREUR" not in result.stdout


def test_ngettext_uses_catalog_plural_forms(toolkit_root):
    from core import i18n

    with i18n.temporary_language("fr"):
        assert i18n.ngettext("{n} fichier", "{n} fichiers", 1) == "{n} fichier"
        assert i18n.ngettext("{n} fichier", "{n} fichiers", 0) == "{n} fichiers"
    with i18n.temporary_language("en"):
        # Pas d'entrée plurielle : gettext retombe sur la règle anglaise n == 1
        assert i18n.ngettext("{n} fichier", "{n} fichiers", 1) == "{n} fichier"
        assert i18n.ngettext("{n} fichier", "{n} fichiers", 2) == "{n} fichiers"
        assert i18n._translation is not None


def test_header_prefixes_are_not_translatable(toolkit_root):
    """Les préfixes d'en-tête relus par le code ne passent pas par le catalogue."""
    from tools.translator import common

    prefixes = [
        common.HEADER_TITLE_PREFIX, common.HEADER_GENERATED_PREFIX, common.HEADER_TOTAL_KEYS_PREFIX,
        common.HEADER_NEW_KEYS_PREFIX, common.HEADER_CHANGED_KEYS_PREFIX, common.HEADER_SOURCE_PREFIX,
        common.HEADER_SEPARATOR_PREFIX,
    ]
    entries = _parse_po(os.path.join(toolkit_root, PO_RELATIVE))
    leaked = [e["msgid"] for e in entries if any(e["msgid"].upper().startswith(p.upper()) for p in prefixes)]
    assert leaked == []
