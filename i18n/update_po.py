#!/usr/bin/env python3
"""
update_po.py - Met à jour les fichiers .po avec les nouvelles chaînes du .pot

Ce script fusionne le template .pot avec les fichiers .po existants,
préservant les traductions existantes tout en ajoutant les nouvelles chaînes.

Usage:
    python scripts/update_po.py           # Met à jour toutes les langues
    python scripts/update_po.py en        # Met à jour uniquement l'anglais

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-02-03
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.colors import Colors

c = Colors()


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
LOCALE_DIR = PROJECT_ROOT / "locale"
POT_FILE = LOCALE_DIR / "messages.pot"


# =============================================================================
# PARSEUR PO/POT
# =============================================================================

class POEntry:
    """Représente une entrée dans un fichier .po/.pot."""

    def __init__(self):
        self.comments: List[str] = []      # Commentaires (#, #., #:, etc.)
        self.flags: List[str] = []         # Flags (#,)
        self.msgid: str = ""
        self.msgstr: str = ""
        self.is_header: bool = False

    def __repr__(self):
        return f"POEntry(msgid={self.msgid[:30]!r}...)"


def parse_po(filepath: Path) -> Tuple[Optional[POEntry], Dict[str, POEntry]]:
    """Parse un fichier .po/.pot.

    Args:
        filepath: Chemin du fichier

    Returns:
        Tuple (header_entry, {msgid: entry})
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = {}
    header = None
    current = POEntry()

    lines = content.split('\n')
    i = 0
    in_msgid = False
    in_msgstr = False

    while i < len(lines):
        line = lines[i]

        # Commentaire
        if line.startswith('#'):
            if line.startswith('#,'):
                # Flags
                flags = line[2:].strip().split(',')
                current.flags.extend(f.strip() for f in flags)
            else:
                current.comments.append(line)
            i += 1
            continue

        # Ligne vide = fin d'entrée
        if not line.strip():
            if current.msgid or current.msgstr:
                if current.msgid == "":
                    current.is_header = True
                    header = current
                else:
                    entries[current.msgid] = current
                current = POEntry()
                in_msgid = False
                in_msgstr = False
            i += 1
            continue

        # msgid
        if line.startswith('msgid '):
            in_msgid = True
            in_msgstr = False
            current.msgid = extract_quoted(line[6:])
            i += 1
            continue

        # msgstr
        if line.startswith('msgstr '):
            in_msgid = False
            in_msgstr = True
            current.msgstr = extract_quoted(line[7:])
            i += 1
            continue

        # Continuation
        if line.strip().startswith('"'):
            text = extract_quoted(line)
            if in_msgid:
                current.msgid += text
            elif in_msgstr:
                current.msgstr += text
            i += 1
            continue

        i += 1

    # Dernière entrée
    if current.msgid or current.msgstr:
        if current.msgid == "":
            current.is_header = True
            header = current
        else:
            entries[current.msgid] = current

    return header, entries


def extract_quoted(s: str) -> str:
    """Extrait le texte entre guillemets."""
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


def escape_string(s: str) -> str:
    """Échappe une chaîne pour le format .po."""
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')
    return s


def format_po_string(text: str, prefix: str = "") -> str:
    """Formate une chaîne pour le fichier .po."""
    escaped = escape_string(text)

    # Si multiligne, utiliser le format avec "" sur la première ligne
    if '\\n' in escaped and len(escaped) > 70:
        lines = escaped.split('\\n')
        result = f'{prefix}""\n'
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                result += f'"{line}\\n"\n'
            elif line:
                result += f'"{line}"\n'
        return result.rstrip('\n')

    return f'{prefix}"{escaped}"'


def write_po_entry(entry: POEntry) -> str:
    """Génère le texte d'une entrée .po."""
    lines = []

    # Commentaires
    for comment in entry.comments:
        lines.append(comment)

    # Flags
    if entry.flags:
        lines.append('#, ' + ', '.join(entry.flags))

    # msgid
    lines.append(format_po_string(entry.msgid, "msgid "))

    # msgstr
    lines.append(format_po_string(entry.msgstr, "msgstr "))

    return '\n'.join(lines)


# =============================================================================
# FUSION
# =============================================================================

def merge_po_with_pot(po_header: Optional[POEntry], po_entries: Dict[str, POEntry],
                       pot_header: Optional[POEntry], pot_entries: Dict[str, POEntry],
                       lang_code: str) -> Tuple[str, dict]:
    """Fusionne un .po avec un .pot.

    Args:
        po_header: En-tête du .po existant
        po_entries: Entrées du .po existant
        pot_header: En-tête du .pot
        pot_entries: Entrées du .pot
        lang_code: Code de la langue

    Returns:
        Tuple (contenu_po, statistiques)
    """
    stats = {
        'kept': 0,      # Traductions conservées
        'new': 0,       # Nouvelles chaînes
        'obsolete': 0,  # Chaînes obsolètes (plus dans le pot)
    }

    # Mettre à jour l'en-tête
    now = datetime.now().strftime("%Y-%m-%d %H:%M%z")
    if po_header:
        # Garder l'en-tête existant mais mettre à jour la date
        header_content = po_header.msgstr
        header_content = re.sub(
            r'"PO-Revision-Date: [^"]*"',
            f'"PO-Revision-Date: {now}"',
            header_content
        )
    else:
        header_content = pot_header.msgstr if pot_header else ""

    header = POEntry()
    header.is_header = True
    header.msgid = ""
    header.msgstr = header_content

    # Construire les nouvelles entrées
    result_entries = []

    for msgid, pot_entry in pot_entries.items():
        new_entry = POEntry()
        new_entry.comments = pot_entry.comments.copy()  # Références du .pot
        new_entry.msgid = msgid

        if msgid in po_entries:
            # Traduction existante
            existing = po_entries[msgid]
            new_entry.msgstr = existing.msgstr
            new_entry.flags = existing.flags.copy()
            stats['kept'] += 1
        else:
            # Nouvelle chaîne
            new_entry.msgstr = ""
            new_entry.flags = ['fuzzy']  # Marquer comme à traduire
            stats['new'] += 1

        result_entries.append(new_entry)

    # Compter les chaînes obsolètes
    for msgid in po_entries:
        if msgid not in pot_entries:
            stats['obsolete'] += 1

    # Générer le contenu
    output_lines = []

    # En-tête
    output_lines.append(write_po_entry(header))
    output_lines.append("")

    # Entrées triées par première référence
    def sort_key(entry):
        for comment in entry.comments:
            if comment.startswith('#:'):
                return comment
        return entry.msgid

    for entry in sorted(result_entries, key=sort_key):
        output_lines.append(write_po_entry(entry))
        output_lines.append("")

    return '\n'.join(output_lines), stats


# =============================================================================
# MAIN
# =============================================================================

def update_language(lang_code: str) -> bool:
    """Met à jour un fichier .po avec le .pot.

    Args:
        lang_code: Code de la langue

    Returns:
        True si succès
    """
    po_file = LOCALE_DIR / lang_code / "LC_MESSAGES" / "messages.po"

    if not po_file.exists():
        print(f"     {c.WARNING}[!] Fichier .po introuvable: {po_file}{c.RESET}")
        return False

    # Parser les fichiers
    pot_header, pot_entries = parse_po(POT_FILE)
    po_header, po_entries = parse_po(po_file)

    # Fusionner
    new_content, stats = merge_po_with_pot(
        po_header, po_entries,
        pot_header, pot_entries,
        lang_code
    )

    # Créer un backup
    backup_file = po_file.with_suffix('.po.bak')
    with open(backup_file, 'w', encoding='utf-8') as f:
        with open(po_file, 'r', encoding='utf-8') as original:
            f.write(original.read())

    # Écrire le nouveau contenu
    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # Afficher les stats
    print(f"     Conservées: {c.VALUE}{stats['kept']}{c.RESET}")
    print(f"     Nouvelles:  {c.VALUE}{stats['new']}{c.RESET} (marquées fuzzy)")
    if stats['obsolete'] > 0:
        print(f"     Obsolètes:  {c.WARNING}{stats['obsolete']}{c.RESET} (supprimées)")

    return True


def main():
    """Point d'entrée principal."""
    print()
    print(c.box_header("MISE À JOUR DES TRADUCTIONS"))
    print()

    # Vérifier le .pot
    if not POT_FILE.exists():
        print(f"{c.ERROR}[X] Fichier template introuvable: {POT_FILE}{c.RESET}")
        print()
        print("Exécutez d'abord: python scripts/extract_strings.py")
        return 1

    # Langue spécifique ou toutes?
    target_lang = sys.argv[1].lower() if len(sys.argv) > 1 else None

    # Trouver les langues à mettre à jour
    languages = []

    for lang_dir in LOCALE_DIR.iterdir():
        if not lang_dir.is_dir():
            continue

        lang_code = lang_dir.name
        if lang_code in ['__pycache__']:
            continue

        if target_lang and lang_code != target_lang:
            continue

        po_file = lang_dir / "LC_MESSAGES" / "messages.po"
        if po_file.exists():
            languages.append(lang_code)

    if not languages:
        if target_lang:
            print(f"{c.WARNING}[!] Langue non trouvée: {target_lang}{c.RESET}")
        else:
            print(f"{c.WARNING}[!] Aucune traduction trouvée dans locale/{c.RESET}")
        return 1

    # Mettre à jour chaque langue
    success = 0

    for lang_code in sorted(languages):
        print(f"{c.INFO}[i] Mise à jour de {lang_code}...{c.RESET}")

        if update_language(lang_code):
            print(f"     {c.OK}[OK]{c.RESET} {lang_code} mis à jour")
            success += 1
        else:
            print(f"     {c.ERROR}[X]{c.RESET} Échec")

        print()

    print(f"{c.OK}[OK] {success}/{len(languages)} langue(s) mise(s) à jour{c.RESET}")
    print()
    print("N'oubliez pas de recompiler: python scripts/compile_po.py")

    return 0 if success == len(languages) else 1


if __name__ == "__main__":
    sys.exit(main())
