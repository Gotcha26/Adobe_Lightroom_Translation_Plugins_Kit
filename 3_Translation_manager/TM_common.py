#!/usr/bin/env python3
"""
TM_common.py

Module commun pour TranslationManager.
Contient les fonctions de parsing, écriture et utilitaires.
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


# =============================================================================
# TRANSLATION WARNING NOTE
# This note is added to all TranslatedStrings_xx.txt files to guide translators
# =============================================================================
TRANSLATION_WARNING_NOTE = """-- -----------------------------------------------------------------------------
-- IMPORTANT NOTES FOR TRANSLATORS:
-- -----------------------------------------------------------------------------
-- 1. DO NOT translate the following patterns (keep them exactly as-is):
--    - %s, %d, %f, %i, %u, %x, %X, %o, %c, %e, %E, %g, %G (format specifiers)
--    - %1, %2, %3... (numbered placeholders)
--    - \\n (newline character)
--    - \\t (tab character)
--    - \\" (escaped quote)
--    - \\\\ (escaped backslash)
--    - ... (ellipsis used as placeholder)
--    - Technical terms in UPPERCASE (API, URL, HTTP, JSON, etc.)
--
-- 2. PRESERVE spaces around text exactly as they appear:
--    - Leading spaces (before text) are used for layout/alignment
--    - Trailing spaces (after text) are used for concatenation
--    - Example: "  Hello  " must keep both leading and trailing spaces
--
-- 3. Keep the same punctuation style (colons, periods, etc.)
-- -----------------------------------------------------------------------------

"""


# =============================================================================
# PARSER
# =============================================================================

def parse_translation_file(file_path: str) -> Dict[str, str]:
    """
    Parse un fichier TranslatedStrings_*.txt
    
    Format: "$$$/Key=Value"
    
    Returns:
        Dict[str, str]: {clé: valeur}
    """
    strings = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Ignorer lignes vides et commentaires
            if not line or line.startswith('--'):
                continue
            
            # Parser: "$$$/Key=Value"
            match = re.match(r'"(\$\$\$/[^"=]+)=([^"]*)"', line)
            if match:
                key = match.group(1)
                value = match.group(2)
                strings[key] = value
    
    return strings


def write_translation_file(file_path: str, lang: str, translations: Dict[str, str],
                           markers: Dict[str, str] = None,
                           metadata: Dict = None):
    """
    Écrit un fichier TranslatedStrings_*.txt
    
    Args:
        file_path: Chemin du fichier
        lang: Code langue
        translations: Dict {clé: valeur}
        markers: Dict {clé: marqueur} pour ajouter des commentaires
        metadata: Dict avec infos supplémentaires pour l'entête
    """
    markers = markers or {}
    metadata = metadata or {}
    
    # Grouper par catégorie
    by_category = defaultdict(list)
    for key in sorted(translations.keys()):
        parts = key.split('/')
        category = parts[1] if len(parts) > 1 else 'General'
        by_category[category].append(key)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("-- =============================================================================\n")
        f.write(f"-- Plugin Localization - {lang.upper()}\n")
        f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Total keys: {len(translations)}\n")
        
        # Infos supplémentaires depuis metadata
        if metadata.get('new_keys'):
            f.write(f"-- New keys: {metadata['new_keys']}\n")
        if metadata.get('changed_keys'):
            f.write(f"-- Changed keys: {metadata['changed_keys']}\n")
        if metadata.get('source'):
            f.write(f"-- Source: {metadata['source']}\n")
        
        f.write("-- =============================================================================\n\n")

        # Add translation warning note for translators
        f.write(TRANSLATION_WARNING_NOTE)

        for category in sorted(by_category.keys()):
            f.write(f"-- {category}\n")
            for key in by_category[category]:
                value = translations[key]
                marker = markers.get(key, '')
                if marker:
                    f.write(f'{marker}\n')
                f.write(f'"{key}={value}"\n')
            f.write("\n")


def resolve_path(path: str) -> Tuple[str, str]:
    """
    Résout un chemin vers (répertoire, fichier).
    
    Accepte:
        - Un fichier .txt directement
        - Un répertoire contenant TranslatedStrings_en.txt
    
    Returns:
        (répertoire, chemin_fichier)
    """
    path = os.path.normpath(path)
    
    if os.path.isfile(path):
        return os.path.dirname(path), path
    elif os.path.isdir(path):
        en_file = os.path.join(path, 'TranslatedStrings_en.txt')
        if os.path.isfile(en_file):
            return path, en_file
        raise FileNotFoundError(f"TranslatedStrings_en.txt non trouvé dans: {path}")
    else:
        raise FileNotFoundError(f"Chemin invalide: {path}")


def load_update_json(update_dir: str) -> Optional[Dict]:
    """
    Charge le fichier UPDATE_en.json depuis un répertoire.
    
    Returns:
        Dict avec les données ou None si non trouvé
    """
    update_file = os.path.join(update_dir, 'UPDATE_en.json')
    if not os.path.isfile(update_file):
        return None
    
    with open(update_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_languages(directory: str, exclude_en: bool = True) -> List[str]:
    """
    Trouve toutes les langues dans un répertoire.
    
    Returns:
        Liste des codes langue (ex: ['fr', 'de', 'es'])
    """
    languages = []
    
    if not os.path.isdir(directory):
        return languages
    
    for file in os.listdir(directory):
        if file.startswith('TranslatedStrings_') and file.endswith('.txt'):
            lang = file.replace('TranslatedStrings_', '').replace('.txt', '')
            if not exclude_en or lang != 'en':
                languages.append(lang)
    
    return sorted(languages)


def clear_screen():
    """Efface l'écran (compatible Windows et Linux)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(version: str = "5.0"):
    """Affiche l'entete du menu."""
    print("\n" + "=" * 70)
    print(f"  TRANSLATION MANAGER v{version}".center(70))
    print("  Gestionnaire de traductions multilingues".center(70))
    print("=" * 70)
