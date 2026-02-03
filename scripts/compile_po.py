#!/usr/bin/env python3
"""
compile_po.py - Compile les fichiers .po en fichiers .mo

Les fichiers .mo sont les fichiers binaires utilisés par gettext
pour la traduction à l'exécution.

Usage:
    python scripts/compile_po.py           # Compile toutes les langues
    python scripts/compile_po.py en        # Compile uniquement l'anglais

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-02-03
"""

import os
import sys
import struct
import array
from pathlib import Path
from typing import List, Tuple

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.colors import Colors

c = Colors()


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
LOCALE_DIR = PROJECT_ROOT / "locale"


# =============================================================================
# COMPILATEUR PO -> MO
# =============================================================================

def parse_po_file(filepath: Path) -> List[Tuple[str, str]]:
    """Parse un fichier .po et retourne les paires msgid/msgstr.

    Args:
        filepath: Chemin du fichier .po

    Returns:
        Liste de tuples (msgid, msgstr)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False

    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Ignorer les commentaires et lignes vides
        if line.startswith('#') or not line:
            # Si on était en train de construire une entrée, la sauvegarder
            if current_msgid is not None and current_msgstr is not None:
                entries.append((current_msgid, current_msgstr))
                current_msgid = None
                current_msgstr = None
                in_msgid = False
                in_msgstr = False
            i += 1
            continue

        # Début d'un msgid
        if line.startswith('msgid '):
            # Sauvegarder l'entrée précédente si elle existe
            if current_msgid is not None and current_msgstr is not None:
                entries.append((current_msgid, current_msgstr))

            in_msgid = True
            in_msgstr = False
            # Extraire le contenu entre guillemets
            current_msgid = extract_string(line[6:])
            current_msgstr = None

        # Début d'un msgstr
        elif line.startswith('msgstr '):
            in_msgid = False
            in_msgstr = True
            current_msgstr = extract_string(line[7:])

        # Continuation d'une chaîne multiligne
        elif line.startswith('"') and line.endswith('"'):
            continuation = extract_string(line)
            if in_msgid and current_msgid is not None:
                current_msgid += continuation
            elif in_msgstr and current_msgstr is not None:
                current_msgstr += continuation

        i += 1

    # Ne pas oublier la dernière entrée
    if current_msgid is not None and current_msgstr is not None:
        entries.append((current_msgid, current_msgstr))

    return entries


def extract_string(s: str) -> str:
    """Extrait une chaîne d'une ligne .po.

    Args:
        s: Ligne contenant une chaîne entre guillemets

    Returns:
        Chaîne extraite et déséchappée
    """
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]

    # Désechapper
    s = s.replace('\\n', '\n')
    s = s.replace('\\r', '\r')
    s = s.replace('\\t', '\t')
    s = s.replace('\\"', '"')
    s = s.replace('\\\\', '\\')

    return s


def generate_mo(entries: List[Tuple[str, str]]) -> bytes:
    """Génère le contenu binaire d'un fichier .mo.

    Format MO:
    - Magic number (4 bytes)
    - Version (4 bytes)
    - Number of strings (4 bytes)
    - Offset of original strings table (4 bytes)
    - Offset of translation strings table (4 bytes)
    - Size of hashing table (4 bytes)
    - Offset of hashing table (4 bytes)

    Args:
        entries: Liste de tuples (msgid, msgstr)

    Returns:
        Contenu binaire du fichier .mo
    """
    # Filtrer les entrées vides et trier par msgid
    entries = [(msgid, msgstr) for msgid, msgstr in entries if msgid or msgstr]
    entries.sort(key=lambda x: x[0])

    # Séparer les chaînes originales et les traductions
    originals = []
    translations = []

    for msgid, msgstr in entries:
        originals.append(msgid.encode('utf-8'))
        translations.append(msgstr.encode('utf-8'))

    # Calculer les offsets
    n_entries = len(entries)
    header_size = 28  # 7 * 4 bytes

    # Tables des descripteurs (length, offset) pour chaque chaîne
    orig_table_offset = header_size
    trans_table_offset = orig_table_offset + n_entries * 8  # 2 * 4 bytes par entrée

    # Les chaînes commencent après les tables
    strings_offset = trans_table_offset + n_entries * 8

    # Construire les chaînes et leurs offsets
    orig_descriptors = []
    trans_descriptors = []
    strings_data = b''

    current_offset = strings_offset

    for orig in originals:
        orig_descriptors.append((len(orig), current_offset))
        strings_data += orig + b'\x00'
        current_offset += len(orig) + 1

    for trans in translations:
        trans_descriptors.append((len(trans), current_offset))
        strings_data += trans + b'\x00'
        current_offset += len(trans) + 1

    # Construire le fichier
    output = bytearray()

    # Header
    output += struct.pack('<I', 0x950412de)  # Magic number (little endian)
    output += struct.pack('<I', 0)            # Version
    output += struct.pack('<I', n_entries)    # Number of strings
    output += struct.pack('<I', orig_table_offset)   # Offset of originals
    output += struct.pack('<I', trans_table_offset)  # Offset of translations
    output += struct.pack('<I', 0)            # Hash table size (unused)
    output += struct.pack('<I', 0)            # Hash table offset (unused)

    # Original strings table
    for length, offset in orig_descriptors:
        output += struct.pack('<II', length, offset)

    # Translation strings table
    for length, offset in trans_descriptors:
        output += struct.pack('<II', length, offset)

    # Strings data
    output += strings_data

    return bytes(output)


def compile_po_file(po_path: Path) -> bool:
    """Compile un fichier .po en .mo.

    Args:
        po_path: Chemin du fichier .po

    Returns:
        True si succès, False sinon
    """
    mo_path = po_path.with_suffix('.mo')

    try:
        entries = parse_po_file(po_path)

        # Compter les traductions non vides
        translated = sum(1 for msgid, msgstr in entries if msgid and msgstr)
        total = sum(1 for msgid, _ in entries if msgid)  # Exclure l'en-tête vide

        mo_content = generate_mo(entries)

        with open(mo_path, 'wb') as f:
            f.write(mo_content)

        return True, translated, total

    except Exception as e:
        print(f"{c.ERROR}[X] Erreur: {e}{c.RESET}")
        return False, 0, 0


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal."""
    print()
    print(c.box_header("COMPILATION DES TRADUCTIONS"))
    print()

    # Langue spécifique ou toutes?
    target_lang = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if not LOCALE_DIR.exists():
        print(f"{c.ERROR}[X] Répertoire locale/ introuvable{c.RESET}")
        return 1

    # Trouver tous les fichiers .po
    po_files = []

    for lang_dir in LOCALE_DIR.iterdir():
        if not lang_dir.is_dir():
            continue

        lang_code = lang_dir.name

        # Filtrer si une langue spécifique est demandée
        if target_lang and lang_code != target_lang:
            continue

        po_file = lang_dir / "LC_MESSAGES" / "messages.po"
        if po_file.exists():
            po_files.append((lang_code, po_file))

    if not po_files:
        if target_lang:
            print(f"{c.WARNING}[!] Aucun fichier .po trouvé pour la langue: {target_lang}{c.RESET}")
        else:
            print(f"{c.WARNING}[!] Aucun fichier .po trouvé dans locale/{c.RESET}")
        return 1

    # Compiler chaque fichier
    success_count = 0

    for lang_code, po_file in sorted(po_files):
        print(f"{c.INFO}[i] Compilation de {lang_code}...{c.RESET}")

        result, translated, total = compile_po_file(po_file)

        if result:
            mo_file = po_file.with_suffix('.mo')
            percent = (translated / total * 100) if total > 0 else 0
            print(f"     {c.OK}[OK]{c.RESET} {mo_file.name} créé ({translated}/{total} = {percent:.0f}%)")
            success_count += 1
        else:
            print(f"     {c.ERROR}[X]{c.RESET} Échec de la compilation")

    print()
    print(f"{c.OK}[OK] {success_count}/{len(po_files)} fichier(s) compilé(s){c.RESET}")

    return 0 if success_count == len(po_files) else 1


if __name__ == "__main__":
    sys.exit(main())
