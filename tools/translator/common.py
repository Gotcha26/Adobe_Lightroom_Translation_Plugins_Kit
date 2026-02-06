#!/usr/bin/env python3
"""
Nom du fichier : common.py

Dépendances : common.colors

Description :
Module commun pour Translator.
Contient les fonctions de parsing, écriture et utilitaires partagées
par tous les modules de traduction (EXTRACT, INJECT, SYNC, COMPARE).

Fournit :
  - Parseurs pour fichiers TranslatedStrings_xx.txt
  - Outils de gestion de chemins et fichiers
  - Utilitaires pour la manipulation des traductions
  - Gestion des logs et des couleurs

Usage CLI :
Non fourni

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.colors import Colors
from .config_loader import get_reference_lang, get_reference_filename, get_update_filename, is_reference_lang

# Instance couleurs
c = Colors()


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
                           markers: Optional[Dict[str, str]] = None,
                           metadata: Optional[Dict] = None):
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


def update_translation_file_surgical(
    target_file: str,
    update_data: Optional[Dict],
    translations: Dict[str, str],
    markers: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict] = None
) -> None:
    """
    Mise à jour chirurgicale d'un fichier de traduction.
    Préserve la structure originale, sections, lignes vides et commentaires.

    Utilise UPDATE_en.json pour appliquer uniquement les changements nécessaires :
    - deleted : Supprime les lignes de clés obsolètes
    - changed : Modifie uniquement la valeur des clés existantes
    - added : Insère les nouvelles clés au bon endroit (après la dernière clé de leur section)

    Args:
        target_file: Chemin du fichier à modifier
        update_data: Données de UPDATE_en.json (peut être None)
        translations: Dict {clé: nouvelle_valeur} avec toutes les traductions
        markers: Dict {clé: marqueur} pour ajouter des commentaires [NEW] ou [NEEDS_REVIEW]
        metadata: Dict avec infos pour l'entête (new_keys, changed_keys, source)
    """
    markers = markers or {}
    metadata = metadata or {}

    # Extraire les changements depuis update_data
    deleted_keys = set(update_data.get('deleted', [])) if update_data else set()
    changed_keys = set(update_data.get('changed', {}).keys()) if update_data else set()
    added_keys = set(update_data.get('added', {}).keys()) if update_data else set()

    # Lire le fichier ligne par ligne
    if not os.path.isfile(target_file):
        # Fichier n'existe pas : utiliser write_translation_file standard
        lang = 'xx'
        basename = os.path.basename(target_file)
        if 'TranslatedStrings_' in basename:
            lang = basename.replace('TranslatedStrings_', '').replace('.txt', '')
        write_translation_file(target_file, lang, translations, markers, metadata)
        return

    with open(target_file, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()

    # Structures pour tracking
    output_lines = []
    keys_processed = set()
    current_section = None
    last_key_in_section = {}  # {section: line_index}
    keys_to_add_by_section = defaultdict(list)  # {section: [keys]}

    # Première passe : identifier les sections et clés à ajouter
    for key in added_keys:
        section = _extract_section_from_key(key)
        keys_to_add_by_section[section].append(key)

    # Deuxième passe : traiter le fichier ligne par ligne
    i = 0
    in_header = True
    header_updated = False

    while i < len(original_lines):
        line = original_lines[i]
        stripped = line.strip()

        # Détecter fin de l'entête
        if in_header and stripped.startswith('-- ') and not stripped.startswith('-- =') and not stripped.startswith('-- -') and not stripped.startswith('-- Plugin') and not stripped.startswith('-- Generated') and not stripped.startswith('-- Total') and not stripped.startswith('-- New') and not stripped.startswith('-- Changed') and not stripped.startswith('-- Source') and not stripped.startswith('-- IMPORTANT'):
            # C'est une section, fin de l'entête
            in_header = False

            # Mettre à jour l'entête si nécessaire
            if not header_updated:
                output_lines = _update_header(output_lines, metadata)
                header_updated = True

        # Détecter les sections (-- SectionName)
        if stripped.startswith('-- ') and not stripped.startswith('-- =') and not stripped.startswith('-- -') and not stripped.startswith('-- IMPORTANT'):
            # Vérifier si c'est vraiment une section (pas un commentaire dans l'entête)
            if not in_header:
                # Avant de changer de section, insérer les clés ajoutées de la section précédente
                if current_section and current_section in keys_to_add_by_section:
                    for key in keys_to_add_by_section[current_section]:
                        if key not in keys_processed:
                            marker = markers.get(key, '')
                            if marker:
                                output_lines.append(f'{marker}\n')
                            output_lines.append(f'"{key}={translations[key]}"\n')
                            keys_processed.add(key)
                    del keys_to_add_by_section[current_section]

                current_section = stripped[3:].strip()  # Enlever "-- "
                output_lines.append(line)
                i += 1
                continue

        # Détecter les clés
        key_match = re.match(r'"(\$\$\$/[^"=]+)=([^"]*)"', stripped)
        if key_match:
            key = key_match.group(1)

            # Clé à supprimer ?
            if key in deleted_keys:
                # Skip cette ligne (et le marqueur précédent s'il existe)
                if output_lines and output_lines[-1].strip().startswith('-- ['):
                    output_lines.pop()  # Retirer le marqueur
                keys_processed.add(key)
                i += 1
                continue

            # Clé à modifier ?
            if key in translations:
                new_value = translations[key]

                # Ajouter marqueur si nécessaire
                marker = markers.get(key, '')
                if marker:
                    output_lines.append(f'{marker}\n')

                # Écrire la clé avec la nouvelle valeur
                output_lines.append(f'"{key}={new_value}"\n')
                keys_processed.add(key)

                # Tracker la dernière clé de cette section
                if current_section:
                    last_key_in_section[current_section] = len(output_lines) - 1

                i += 1
                continue

        # Ligne standard (commentaire, ligne vide, entête)
        output_lines.append(line)
        i += 1

    # Ajouter les clés restantes de la dernière section
    if current_section and current_section in keys_to_add_by_section:
        for key in keys_to_add_by_section[current_section]:
            if key not in keys_processed:
                marker = markers.get(key, '')
                if marker:
                    output_lines.append(f'{marker}\n')
                output_lines.append(f'"{key}={translations[key]}"\n')
                keys_processed.add(key)
        del keys_to_add_by_section[current_section]

    # Ajouter les clés orphelines (sections non trouvées dans le fichier)
    for section, keys in keys_to_add_by_section.items():
        if keys:
            # Créer une nouvelle section
            output_lines.append(f'\n-- {section}\n')
            for key in keys:
                if key not in keys_processed:
                    marker = markers.get(key, '')
                    if marker:
                        output_lines.append(f'{marker}\n')
                    output_lines.append(f'"{key}={translations[key]}"\n')
                    keys_processed.add(key)

    # Écrire le fichier final
    with open(target_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)


def _extract_section_from_key(key: str) -> str:
    """
    Extrait le nom de section depuis une clé.
    Ex: $$$/Piwigo/API/AddTags -> API
        $$$/FionaBoston/Title -> FionaBoston
    """
    parts = key.split('/')
    if len(parts) >= 3:
        return parts[2]  # $$$/Piwigo/API/... -> API
    elif len(parts) == 2:
        return parts[1]  # $$$/FionaBoston/... -> FionaBoston
    return 'General'


def _update_header(header_lines: List[str], metadata: Dict) -> List[str]:
    """
    Met à jour les métadonnées dans l'entête.
    Remplace Generated, Total keys, New keys, Changed keys, Source.
    """
    updated = []
    generated_updated = False
    total_keys_found = False
    new_keys_found = False
    changed_keys_found = False
    source_found = False

    for line in header_lines:
        stripped = line.strip()

        # Remplacer Generated
        if stripped.startswith('-- Generated:'):
            updated.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            generated_updated = True
        # Remplacer Total keys
        elif stripped.startswith('-- Total keys:'):
            total_keys_found = True
            if metadata.get('total_keys') is not None:
                updated.append(f"-- Total keys: {metadata['total_keys']}\n")
            else:
                updated.append(line)
        # Remplacer ou supprimer New keys
        elif stripped.startswith('-- New keys:'):
            new_keys_found = True
            if metadata.get('new_keys'):
                updated.append(f"-- New keys: {metadata['new_keys']}\n")
        # Remplacer ou supprimer Changed keys
        elif stripped.startswith('-- Changed keys:'):
            changed_keys_found = True
            if metadata.get('changed_keys'):
                updated.append(f"-- Changed keys: {metadata['changed_keys']}\n")
        # Remplacer Source
        elif stripped.startswith('-- Source:') or stripped.startswith('-- SOURCE:'):
            source_found = True
            if metadata.get('source'):
                updated.append(f"-- Source: {metadata['source']}\n")
            else:
                updated.append(line)
        else:
            updated.append(line)

    # Ajouter les métadonnées manquantes (avant la ligne de séparation finale)
    insert_index = len(updated)
    for i in range(len(updated) - 1, -1, -1):
        if updated[i].strip().startswith('-- ='):
            insert_index = i
            break

    additions = []
    if not new_keys_found and metadata.get('new_keys'):
        additions.append(f"-- New keys: {metadata['new_keys']}\n")
    if not changed_keys_found and metadata.get('changed_keys'):
        additions.append(f"-- Changed keys: {metadata['changed_keys']}\n")
    if not source_found and metadata.get('source'):
        additions.append(f"-- Source: {metadata['source']}\n")

    if additions:
        updated = updated[:insert_index] + additions + updated[insert_index:]

    return updated


def resolve_path(path: str) -> Tuple[str, str]:
    """
    Résout un chemin vers (répertoire, fichier).

    Accepte:
        - Un fichier .txt directement
        - Un répertoire contenant le fichier de référence (basé sur config.json["lang"])

    Returns:
        (répertoire, chemin_fichier)
    """
    path = os.path.normpath(path)

    if os.path.isfile(path):
        return os.path.dirname(path), path
    elif os.path.isdir(path):
        ref_filename = get_reference_filename()
        ref_file = os.path.join(path, ref_filename)
        if os.path.isfile(ref_file):
            return path, ref_file
        raise FileNotFoundError(f"{ref_filename} non trouvé dans: {path}")
    else:
        raise FileNotFoundError(f"Chemin invalide: {path}")


def load_update_json(update_dir: str) -> Optional[Dict]:
    """
    Charge le fichier UPDATE (basé sur config.json["lang"]) depuis un répertoire.

    Returns:
        Dict avec les données ou None si non trouvé
    """
    update_filename = get_update_filename()
    update_file = os.path.join(update_dir, update_filename)
    if not os.path.isfile(update_file):
        return None

    with open(update_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_languages(directory: str, exclude_reference: bool = True) -> List[str]:
    """
    Trouve toutes les langues dans un répertoire.

    Args:
        directory: Répertoire à scanner
        exclude_reference: Si True, exclut la langue de référence (config.json["lang"])

    Returns:
        Liste des codes langue (ex: ['fr', 'de', 'es'])
    """
    languages = []

    if not os.path.isdir(directory):
        return languages

    reference_lang = get_reference_lang()

    for file in os.listdir(directory):
        if file.startswith('TranslatedStrings_') and file.endswith('.txt'):
            lang = file.replace('TranslatedStrings_', '').replace('.txt', '')
            if not exclude_reference or lang != reference_lang:
                languages.append(lang)

    return sorted(languages)


def clear_screen():
    """Efface l'écran (compatible Windows et Linux)."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(version: str = "6.0"):
    """Affiche l'entete du menu avec couleurs."""
    print()
    print(c.HEADER + "=" * 70 + c.RESET)
    title = f"  TRANSLATION MANAGER v{version}".center(70)
    subtitle = "  Gestionnaire de traductions multilingues".center(70)
    print(c.TITLE + title + c.RESET)
    print(c.DIM + subtitle + c.RESET)
    print(c.HEADER + "=" * 70 + c.RESET)
