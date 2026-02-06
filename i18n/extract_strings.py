#!/usr/bin/env python3
"""
Nom du fichier : extract_strings.py

Dépendances : core.colors

Description :
Extrait les chaînes traduisibles marquées avec _() de tous les fichiers Python
du projet et génère un fichier template de traduction (.pot).
Parcourt récursivement les répertoires configurés en ignorant les dossiers spécifiés.

Usage CLI :
    python i18n/extract_strings.py

Date : 2026-02-06
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Set

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.colors import Colors

c = Colors()


# =============================================================================
# CONFIGURATION
# =============================================================================

# Répertoire racine du projet
PROJECT_ROOT = Path(__file__).parent.parent

# Fichier de sortie
OUTPUT_FILE = PROJECT_ROOT / "locale" / "messages.pot"

# Dossiers à scanner
SCAN_DIRS = [
    PROJECT_ROOT,
    PROJECT_ROOT / "core",
    PROJECT_ROOT / "tools",
    PROJECT_ROOT / "assets",
]

# Dossiers à ignorer
IGNORE_DIRS = {"scripts", "locale", "__pycache__", ".git", "venv", ".venv"}

# Pattern pour trouver les appels _("...")
# Supporte: _("texte"), _('texte'), _("""texte"""), _('''texte''')
GETTEXT_PATTERN = re.compile(
    r'_\(\s*'
    r'(?:'
    r'"""((?:[^"\\]|\\.|"(?!""))*?)"""|'  # Triple double quotes
    r"'''((?:[^'\\]|\\.|'(?!''))*?)'''|"  # Triple single quotes
    r'"((?:[^"\\]|\\.)*)"|'               # Double quotes
    r"'((?:[^'\\]|\\.)*)'"                # Single quotes
    r')\s*\)',
    re.DOTALL
)


# =============================================================================
# EXTRACTION
# =============================================================================

def extract_strings_from_file(filepath: Path) -> List[Tuple[int, str]]:
    """Extrait les chaînes _() d'un fichier Python.

    Args:
        filepath: Chemin du fichier à analyser

    Returns:
        Liste de tuples (numéro_ligne, chaîne)
    """
    strings = []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"{c.WARNING}[!] Impossible de lire {filepath}: {e}{c.RESET}")
        return []

    # Trouver toutes les correspondances
    for match in GETTEXT_PATTERN.finditer(content):
        # Récupérer le groupe non-None (selon le type de guillemets)
        text = match.group(1) or match.group(2) or match.group(3) or match.group(4)

        if text:
            # Calculer le numéro de ligne
            line_num = content[:match.start()].count('\n') + 1
            strings.append((line_num, text))

    return strings


def scan_directory(directory: Path) -> dict:
    """Scanne un répertoire pour extraire les chaînes.

    Args:
        directory: Répertoire à scanner

    Returns:
        Dict {chemin_relatif: [(ligne, chaîne), ...]}
    """
    results = {}

    for root, dirs, files in os.walk(directory):
        # Filtrer les dossiers à ignorer
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in files:
            if not filename.endswith('.py'):
                continue

            filepath = Path(root) / filename
            strings = extract_strings_from_file(filepath)

            if strings:
                # Chemin relatif depuis la racine du projet
                rel_path = filepath.relative_to(PROJECT_ROOT)
                results[str(rel_path)] = strings

    return results


def escape_string(s: str) -> str:
    """Échappe une chaîne pour le format .po.

    Args:
        s: Chaîne à échapper

    Returns:
        Chaîne échappée
    """
    # Échapper les backslashes d'abord
    s = s.replace('\\', '\\\\')
    # Échapper les guillemets
    s = s.replace('"', '\\"')
    # Échapper les retours à la ligne
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    # Échapper les tabulations
    s = s.replace('\t', '\\t')
    return s


def format_msgid(text: str) -> str:
    """Formate un msgid pour le fichier .po.

    Gère les chaînes multilignes.

    Args:
        text: Texte à formater

    Returns:
        Texte formaté pour .po
    """
    escaped = escape_string(text)

    # Si la chaîne contient des \n, utiliser le format multiligne
    if '\\n' in escaped:
        lines = escaped.split('\\n')
        result = '""' + '\n'
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                result += f'"{line}\\n"\n'
            else:
                if line:  # Ne pas ajouter de ligne vide à la fin
                    result += f'"{line}"\n'
        return result.rstrip('\n')
    else:
        return f'"{escaped}"'


def generate_pot_content(all_strings: dict) -> str:
    """Génère le contenu du fichier .pot.

    Args:
        all_strings: Dict {fichier: [(ligne, chaîne), ...]}

    Returns:
        Contenu du fichier .pot
    """
    # En-tête du fichier .pot
    now = datetime.now().strftime("%Y-%m-%d %H:%M%z")

    header = f'''# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: LocalisationToolKit 2.1\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: {now}\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

'''

    # Collecter toutes les chaînes uniques avec leurs références
    # Dict {chaîne: [références]}
    unique_strings: dict = {}

    for filepath, strings in sorted(all_strings.items()):
        for line_num, text in strings:
            if text not in unique_strings:
                unique_strings[text] = []
            unique_strings[text].append(f"{filepath}:{line_num}")

    # Générer les entrées
    entries = []
    for text, refs in sorted(unique_strings.items(), key=lambda x: (x[1][0] if x[1] else "", x[0])):
        # Références (commentaires #:)
        ref_comments = "\n".join(f"#: {ref}" for ref in refs)

        # msgid et msgstr
        msgid = format_msgid(text)
        entry = f'{ref_comments}\nmsgid {msgid}\nmsgstr ""\n'
        entries.append(entry)

    return header + "\n".join(entries)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal."""
    print()
    print(c.box_header("EXTRACTION DES CHAÎNES TRADUISIBLES"))
    print()

    # Scanner les répertoires
    print(f"{c.INFO}[i] Scan des fichiers Python...{c.RESET}")

    all_strings = {}
    total_strings = 0
    total_files = 0

    for directory in SCAN_DIRS:
        if directory.exists():
            results = scan_directory(directory)
            for filepath, strings in results.items():
                if filepath not in all_strings:
                    all_strings[filepath] = strings
                    total_strings += len(strings)
                    total_files += 1

    print(f"     Fichiers analysés: {c.VALUE}{total_files}{c.RESET}")
    print(f"     Chaînes trouvées:  {c.VALUE}{total_strings}{c.RESET}")

    if total_strings == 0:
        print()
        print(f"{c.WARNING}[!] Aucune chaîne _() trouvée.{c.RESET}")
        print(f"    Assurez-vous d'avoir ajouté les appels _() dans le code.")
        return 1

    # Compter les chaînes uniques
    unique = set()
    for strings in all_strings.values():
        for _, text in strings:
            unique.add(text)
    print(f"     Chaînes uniques:   {c.VALUE}{len(unique)}{c.RESET}")

    # Créer le répertoire locale/ si nécessaire
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Générer le fichier .pot
    print()
    print(f"{c.INFO}[i] Génération de {OUTPUT_FILE.name}...{c.RESET}")

    content = generate_pot_content(all_strings)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"     {c.OK}[OK]{c.RESET} Fichier créé: {c.VALUE}{OUTPUT_FILE}{c.RESET}")

    # Afficher les fichiers traités
    print()
    print(f"{c.DIM}Fichiers contenant des chaînes traduisibles:{c.RESET}")
    for filepath in sorted(all_strings.keys()):
        count = len(all_strings[filepath])
        print(f"     {filepath}: {count} chaîne(s)")

    print()
    print(f"{c.OK}[OK] Extraction terminée!{c.RESET}")
    print()
    print(f"Prochaine étape:")
    print(f"  1. Créer une traduction: python scripts/init_language.py <lang>")
    print(f"  2. Éditer le fichier .po avec un éditeur (ex: Poedit)")
    print(f"  3. Compiler: python scripts/compile_po.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
