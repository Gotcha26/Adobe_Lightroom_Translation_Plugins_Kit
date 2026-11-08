#!/usr/bin/env python3
"""
Nom du fichier : common.py

Dépendances : core.colors

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

Date : 2026-11-08
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
from core import __version__
from core.cli import clear_screen  # noqa: F401 (réexporté pour les modules du Translator)
from core.colors import c
from core.i18n import _
from .config_loader import get_reference_lang, get_reference_filename, get_update_filename


# =============================================================================
# MARQUEURS DU FORMAT TRANSLATE_xx.txt (jamais traduits : lus par la machine)
# =============================================================================

TRANSLATE_KEY = "[KEY]"
TRANSLATE_ARROW = "→"


def translate_ref_marker(lang: str) -> str:
    return f"[{lang.upper()}]"


def translate_before_marker(lang: str) -> str:
    return f"[{lang.upper()} BEFORE]"


def translate_after_marker(lang: str) -> str:
    return f"[{lang.upper()} AFTER]"


def translate_target_marker(lang: str) -> str:
    return f"[{lang.upper()}] {TRANSLATE_ARROW} "


# =============================================================================
# EN-TÊTE DES FICHIERS TranslatedStrings_xx.txt (jamais traduit : relu par la machine)
# =============================================================================

HEADER_SEPARATOR = "-- " + "=" * 77
HEADER_SEPARATOR_PREFIX = "-- ===="
HEADER_TITLE_PREFIX = "-- Plugin Localization -"
HEADER_GENERATED_PREFIX = "-- Generated:"
HEADER_TOTAL_KEYS_PREFIX = "-- Total keys:"
HEADER_NEW_KEYS_PREFIX = "-- New keys:"
HEADER_CHANGED_KEYS_PREFIX = "-- Changed keys:"
HEADER_SOURCE_PREFIX = "-- Source:"

# Marqueurs posés par SYNC au-dessus d'une clé, relus par AUTOSYNC et la mise à
# jour chirurgicale : seul le préfixe est fixe, le commentaire qui suit est traduit
MARKER_NEW = "-- [NEW]"
MARKER_NEEDS_REVIEW = "-- [NEEDS_REVIEW]"
MARKER_PREFIXES = (MARKER_NEW, MARKER_NEEDS_REVIEW)


def is_marker_line(line: str) -> bool:
    """Vrai si la ligne est un marqueur [NEW] / [NEEDS_REVIEW] posé par SYNC."""
    return line.strip().startswith(MARKER_PREFIXES)


def _header_line(prefix: str, value) -> str:
    """Ligne d'en-tête « prefix value » terminée par un saut de ligne."""
    return f"{prefix} {value}\n"




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

# Ligne clé/valeur : "$$$/Key=Value". La valeur peut contenir des séquences
# d'échappement (\" et \\), conservées telles quelles.
KEY_LINE_RE = re.compile(r'"(\$\$\$/[^"=]+)=((?:[^"\\]|\\.)*)"')

# Ligne de section : "-- Nom" (un seul mot ; exclut marqueurs "-- [NEW] ..." et séparateurs)
SECTION_LINE_RE = re.compile(r'^--\s+(\w[\w.-]*)$')

# Séquences d'échappement reconnues dans une valeur ("\" suivi de l'un de ces caractères)
VALID_ESCAPES = '"\\nrt'


def escape_translation_value(value: str) -> str:
    """
    Échappe une traduction saisie à la main pour qu'elle reste relisible par KEY_LINE_RE.

    - `"` non précédé d'un `\\` devient `\\"` ;
    - un `\\` qui n'ouvre pas une séquence valide (`\\"`, `\\\\`, `\\n`, `\\r`, `\\t`)
      devient `\\\\` ;
    - les séquences déjà valides sont conservées telles quelles (idempotent).
    """
    out = []
    i = 0
    while i < len(value):
        ch = value[i]
        if ch == '\\':
            if i + 1 < len(value) and value[i + 1] in VALID_ESCAPES:
                out.append(value[i:i + 2])
                i += 2
                continue
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        else:
            out.append(ch)
        i += 1
    return ''.join(out)


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
            # La valeur peut contenir des guillemets échappés (\") et des
            # backslashes échappés (\\) ; on accepte donc soit un caractère
            # non spécial, soit une séquence d'échappement \X. Les escapes
            # sont conservés tels quels dans la valeur — l'écriture symétrique
            # via write_translation_file les préserve.
            match = KEY_LINE_RE.match(line)
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
        by_category[section_for_key(key)].append(key)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(HEADER_SEPARATOR + "\n")
        f.write(_header_line(HEADER_TITLE_PREFIX, lang.upper()))
        f.write(_header_line(HEADER_GENERATED_PREFIX, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write(_header_line(HEADER_TOTAL_KEYS_PREFIX, len(translations)))

        # Infos supplémentaires depuis metadata
        if metadata.get('new_keys'):
            f.write(_header_line(HEADER_NEW_KEYS_PREFIX, metadata['new_keys']))
        if metadata.get('changed_keys'):
            f.write(_header_line(HEADER_CHANGED_KEYS_PREFIX, metadata['changed_keys']))
        if metadata.get('source'):
            f.write(_header_line(HEADER_SOURCE_PREFIX, metadata['source']))

        f.write(HEADER_SEPARATOR + "\n\n")

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
    metadata: Optional[Dict] = None,
    remove_unlisted: bool = False
) -> None:
    """
    Mise à jour chirurgicale d'un fichier de traduction.
    Préserve la structure originale, sections, lignes vides et commentaires.

    Structure reconnue :
    - en-tête : du début du fichier jusqu'à la deuxième ligne « -- ==== » incluse
      (ses métadonnées sont mises à jour via _update_header) ;
    - note aux traducteurs : bloc commençant à la première ligne « -- ---- » qui
      suit l'en-tête, recopié tel quel et jamais interprété comme section ;
    - sections : lignes « -- <mot> » rencontrées après ces deux blocs.

    Utilise UPDATE_<lang>.json pour appliquer uniquement les changements nécessaires :
    - deleted : Supprime les lignes de clés obsolètes
    - changed : Modifie uniquement la valeur des clés existantes
    - added : Insère les nouvelles clés au bon endroit (après la dernière clé de leur section)

    Args:
        target_file: Chemin du fichier à modifier
        update_data: Données de UPDATE_<lang>.json (peut être None)
        translations: Dict {clé: nouvelle_valeur} avec toutes les traductions
        markers: Dict {clé: marqueur} pour ajouter des commentaires [NEW] ou [NEEDS_REVIEW]
        metadata: Dict avec infos pour l'entête (new_keys, changed_keys, source, total_keys)
        remove_unlisted: Si True, `translations` décrit le contenu complet attendu :
            les clés du fichier absentes de `translations` sont supprimées et les
            clés de `translations` absentes du fichier sont ajoutées.
    """
    markers = markers or {}
    metadata = metadata or {}

    # Extraire les changements depuis update_data
    deleted_keys = set(update_data.get('deleted', [])) if update_data else set()
    added_keys = set(update_data.get('added', {}).keys()) if update_data else set()

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

    if original_lines and not original_lines[-1].endswith('\n'):
        original_lines[-1] += '\n'

    header_end, body_start = _locate_header_and_note(original_lines)

    # En-tête (métadonnées mises à jour) puis note aux traducteurs recopiée telle quelle
    output_lines = _update_header(original_lines[:header_end], metadata) if header_end else []
    output_lines.extend(original_lines[header_end:body_start])

    current_section = None
    section_insert_pos = {}  # {section: index d'insertion après sa dernière clé}
    keys_in_file = set()

    for line in original_lines[body_start:]:
        stripped = line.strip()

        # Section (-- Nom)
        section_match = SECTION_LINE_RE.match(stripped)
        if section_match:
            current_section = section_match.group(1)
            output_lines.append(line)
            section_insert_pos[current_section] = len(output_lines)
            continue

        key_match = KEY_LINE_RE.match(stripped)
        if key_match:
            key = key_match.group(1)
            keys_in_file.add(key)

            # Clé à supprimer (obsolète ou absente des traductions attendues)
            if key in deleted_keys or (remove_unlisted and key not in translations):
                # Retirer aussi le marqueur qui la précède s'il existe
                if output_lines and is_marker_line(output_lines[-1]):
                    output_lines.pop()
                continue

            if key in translations:
                marker = markers.get(key, '')
                if marker:
                    # Remplacer le marqueur déjà présent au-dessus de la clé au lieu
                    # de l'empiler (relances successives de SYNC)
                    if output_lines and is_marker_line(output_lines[-1]):
                        output_lines.pop()
                    output_lines.append(f'{marker}\n')
                # Sans marqueur demandé, un marqueur existant est conservé : c'est
                # un repère pour le traducteur (INJECT ne transmet jamais de marqueurs)
                output_lines.append(f'"{key}={translations[key]}"\n')
            else:
                output_lines.append(line)

            if current_section is not None:
                section_insert_pos[current_section] = len(output_lines)
            continue

        # Ligne standard (commentaire, ligne vide)
        output_lines.append(line)

    # Clés à ajouter, regroupées par section
    keys_to_add = set(added_keys)
    if remove_unlisted:
        keys_to_add |= set(translations)
    keys_to_add_by_section = defaultdict(list)
    for key in sorted(keys_to_add - keys_in_file):
        if key in translations:
            keys_to_add_by_section[section_for_key(key)].append(key)

    def _key_lines(keys: List[str]) -> List[str]:
        lines = []
        for key in keys:
            marker = markers.get(key, '')
            if marker:
                lines.append(f'{marker}\n')
            lines.append(f'"{key}={translations[key]}"\n')
        return lines

    # Sections existantes : insertion après leur dernière clé (de la fin vers le début
    # pour ne pas décaler les positions restant à traiter)
    existing = [s for s in keys_to_add_by_section if s in section_insert_pos]
    for section in sorted(existing, key=lambda s: section_insert_pos[s], reverse=True):
        pos = section_insert_pos[section]
        output_lines[pos:pos] = _key_lines(keys_to_add_by_section.pop(section))

    # Sections absentes du fichier : créées en fin de fichier
    for section in sorted(keys_to_add_by_section):
        if output_lines and output_lines[-1].strip():
            output_lines.append('\n')
        output_lines.append(f'-- {section}\n')
        output_lines.extend(_key_lines(keys_to_add_by_section[section]))
        output_lines.append('\n')

    with open(target_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)


def _locate_header_and_note(lines: List[str]) -> Tuple[int, int]:
    """
    Repère l'en-tête et la note aux traducteurs.

    Returns:
        (fin_entete, debut_corps) : indices de ligne (exclusifs). fin_entete vaut 0
        si le fichier n'a pas d'en-tête reconnaissable (deux lignes « -- ==== »).
        debut_corps est la première ligne après la note (ou après l'en-tête).
    """
    header_end = 0
    separators = 0
    for idx, line in enumerate(lines):
        if line.strip().startswith(HEADER_SEPARATOR_PREFIX):
            separators += 1
            if separators == 2:
                header_end = idx + 1
                break

    # Note : commence à la première ligne « -- ---- » qui suit l'en-tête (seules des
    # lignes vides peuvent les séparer) et s'étend jusqu'à la dernière ligne
    # « -- ---- » précédant la première clé.
    idx = header_end
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines) or not lines[idx].strip().startswith('-- ----'):
        return header_end, header_end

    note_end = idx + 1
    for j in range(idx + 1, len(lines)):
        stripped = lines[j].strip()
        if KEY_LINE_RE.match(stripped):
            break
        if stripped.startswith('-- ----'):
            note_end = j + 1
    return header_end, note_end


def section_for_key(key: str) -> str:
    """
    Nom de section d'une clé (partagé par Translator et Extractor).
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
    new_keys_found = False
    changed_keys_found = False
    source_found = False

    for line in header_lines:
        stripped = line.strip()

        # Remplacer Generated
        if stripped.startswith(HEADER_GENERATED_PREFIX):
            updated.append(_header_line(HEADER_GENERATED_PREFIX, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # Remplacer Total keys
        elif stripped.startswith(HEADER_TOTAL_KEYS_PREFIX):
            if metadata.get('total_keys') is not None:
                updated.append(_header_line(HEADER_TOTAL_KEYS_PREFIX, metadata['total_keys']))
            else:
                updated.append(line)
        # Remplacer ou supprimer New keys
        elif stripped.startswith(HEADER_NEW_KEYS_PREFIX):
            new_keys_found = True
            if metadata.get('new_keys'):
                updated.append(_header_line(HEADER_NEW_KEYS_PREFIX, metadata['new_keys']))
        # Remplacer ou supprimer Changed keys
        elif stripped.startswith(HEADER_CHANGED_KEYS_PREFIX):
            changed_keys_found = True
            if metadata.get('changed_keys'):
                updated.append(_header_line(HEADER_CHANGED_KEYS_PREFIX, metadata['changed_keys']))
        # Remplacer Source (« -- SOURCE: » : graphie écrite par l'Extractor)
        elif stripped.startswith(HEADER_SOURCE_PREFIX) or stripped.startswith(HEADER_SOURCE_PREFIX.upper()):
            source_found = True
            if metadata.get('source'):
                updated.append(_header_line(HEADER_SOURCE_PREFIX, metadata['source']))
            else:
                updated.append(line)
        else:
            updated.append(line)

    # Ajouter les métadonnées manquantes (avant la ligne de séparation finale)
    insert_index = len(updated)
    for i in range(len(updated) - 1, -1, -1):
        if updated[i].strip().startswith(HEADER_SEPARATOR_PREFIX):
            insert_index = i
            break

    additions = []
    if not new_keys_found and metadata.get('new_keys'):
        additions.append(_header_line(HEADER_NEW_KEYS_PREFIX, metadata['new_keys']))
    if not changed_keys_found and metadata.get('changed_keys'):
        additions.append(_header_line(HEADER_CHANGED_KEYS_PREFIX, metadata['changed_keys']))
    if not source_found and metadata.get('source'):
        additions.append(_header_line(HEADER_SOURCE_PREFIX, metadata['source']))

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
        raise FileNotFoundError(_("{ref_filename} non trouvé dans: {path}").format(ref_filename=ref_filename, path=path))
    else:
        raise FileNotFoundError(_("Chemin invalide: {path}").format(path=path))


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


def print_header(version: str = None):
    """Affiche l'entete du menu avec couleurs."""
    if version is None:
        version = __version__
    print()
    print(c.HEADER + "=" * 70 + c.RESET)
    title = _("  TRANSLATION MANAGER v{version}").format(version=version).center(70)
    subtitle = _("  Gestionnaire de traductions multilingues").center(70)
    print(c.TITLE + title + c.RESET)
    print(c.DIM + subtitle + c.RESET)
    print(c.HEADER + "=" * 70 + c.RESET)
