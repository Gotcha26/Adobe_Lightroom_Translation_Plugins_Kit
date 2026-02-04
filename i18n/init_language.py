#!/usr/bin/env python3
"""
Nom du fichier : init_language.py

Dépendances : core.colors

Description :
Initialise une nouvelle langue de traduction en créant la structure de dossiers
et le fichier .po initial pour une langue à partir du template .pot.
Met à jour les métadonnées du fichier .po avec les informations de la langue.

Usage CLI :
    python i18n/init_language.py <code_langue>
    python i18n/init_language.py en    # Anglais
    python i18n/init_language.py es    # Espagnol
    python i18n/init_language.py de    # Allemand

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

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

# Noms des langues pour l'affichage
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Español",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "nl": "Nederlands",
    "pl": "Polski",
    "ru": "Русский",
    "ja": "日本語",
    "zh": "中文",
    "ko": "한국어",
}


# =============================================================================
# FONCTIONS
# =============================================================================

def create_po_file(lang_code: str, pot_content: str) -> str:
    """Crée le contenu du fichier .po à partir du .pot.

    Args:
        lang_code: Code de la langue
        pot_content: Contenu du fichier .pot

    Returns:
        Contenu du fichier .po
    """
    lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
    now = datetime.now().strftime("%Y-%m-%d %H:%M%z")

    # Remplacer l'en-tête
    po_content = pot_content

    # Mettre à jour les métadonnées
    replacements = [
        ('# SOME DESCRIPTIVE TITLE.', f'# {lang_name} translations for LocalisationToolKit'),
        ('# Copyright (C) YEAR', f'# Copyright (C) {datetime.now().year}'),
        ('# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.', '# Translator <translator@email.com>, ' + str(datetime.now().year)),
        ('#, fuzzy\n', ''),  # Retirer le flag fuzzy de l'en-tête
        ('YEAR-MO-DA HO:MI+ZONE', now),
        ('FULL NAME <EMAIL@ADDRESS>', 'Translator'),
        ('LANGUAGE <LL@li.org>', f'{lang_name} <{lang_code}@li.org>'),
        ('"Language: \\n"', f'"Language: {lang_code}\\n"'),
    ]

    for old, new in replacements:
        po_content = po_content.replace(old, new)

    return po_content


def init_language(lang_code: str) -> int:
    """Initialise une nouvelle langue.

    Args:
        lang_code: Code de la langue (ex: "en", "es")

    Returns:
        Code de retour (0 = succès)
    """
    print()
    print(c.box_header(f"INITIALISATION DE LA LANGUE: {lang_code.upper()}"))
    print()

    # Vérifier que le .pot existe
    if not POT_FILE.exists():
        print(f"{c.ERROR}[X] Fichier template introuvable: {POT_FILE}{c.RESET}")
        print()
        print("Exécutez d'abord: python scripts/extract_strings.py")
        return 1

    # Créer le répertoire de la langue
    lang_dir = LOCALE_DIR / lang_code / "LC_MESSAGES"

    if lang_dir.exists():
        print(f"{c.WARNING}[!] Le répertoire existe déjà: {lang_dir}{c.RESET}")

        # Vérifier si le .po existe
        po_file = lang_dir / "messages.po"
        if po_file.exists():
            print(f"     Le fichier {po_file.name} existe déjà.")
            response = input(f"\n{c.PROMPT}Écraser? [o/N]: {c.RESET}").strip().lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                print(f"{c.INFO}[i] Opération annulée.{c.RESET}")
                return 0
    else:
        print(f"{c.INFO}[i] Création du répertoire: {lang_dir}{c.RESET}")
        lang_dir.mkdir(parents=True, exist_ok=True)

    # Lire le .pot
    with open(POT_FILE, 'r', encoding='utf-8') as f:
        pot_content = f.read()

    # Créer le .po
    po_content = create_po_file(lang_code, pot_content)

    po_file = lang_dir / "messages.po"
    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(po_content)

    print(f"     {c.OK}[OK]{c.RESET} Fichier créé: {c.VALUE}{po_file}{c.RESET}")

    # Compter les chaînes à traduire
    msgid_count = pot_content.count('\nmsgid "') - 1  # -1 pour l'en-tête
    print(f"     Chaînes à traduire: {c.VALUE}{msgid_count}{c.RESET}")

    # Mettre à jour la liste des langues supportées
    print()
    print(f"{c.INFO}[i] N'oubliez pas de mettre à jour SUPPORTED_LANGUAGES dans common/i18n.py{c.RESET}")
    print(f"     Ajoutez '{lang_code}' à la liste si ce n'est pas déjà fait.")

    print()
    print(f"{c.OK}[OK] Langue {lang_code} initialisée!{c.RESET}")
    print()
    print("Prochaines étapes:")
    print(f"  1. Éditez le fichier: {po_file}")
    print(f"  2. Remplissez les msgstr avec les traductions")
    print(f"  3. Compilez: python scripts/compile_po.py")

    return 0


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print()
        print(c.box_header("INITIALISATION D'UNE LANGUE"))
        print()
        print("Usage: python scripts/init_language.py <code_langue>")
        print()
        print("Exemples:")
        print("  python scripts/init_language.py en    # Anglais")
        print("  python scripts/init_language.py es    # Espagnol")
        print("  python scripts/init_language.py de    # Allemand")
        print()
        print("Langues connues:")
        for code, name in sorted(LANGUAGE_NAMES.items()):
            print(f"  {code}: {name}")
        return 1

    lang_code = sys.argv[1].lower().strip()

    # Validation basique
    if len(lang_code) < 2 or len(lang_code) > 5:
        print(f"{c.ERROR}[X] Code langue invalide: {lang_code}{c.RESET}")
        print("    Utilisez un code ISO 639-1 (ex: en, fr, es)")
        return 1

    return init_language(lang_code)


if __name__ == "__main__":
    sys.exit(main())
