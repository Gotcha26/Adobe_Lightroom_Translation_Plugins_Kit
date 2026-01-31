#!/usr/bin/env python3
"""
WebBridge_export.py

Export des fichiers Lightroom SDK vers le format JSON i18n.

Fonctions principales:
    - load_translated_strings: Charge un fichier TranslatedStrings_xx.txt
    - load_spacing_metadata: Charge le fichier spacing_metadata.json
    - load_extraction_report: Charge le fichier extraction_report.txt
    - export_to_i18n: Exporte vers le format JSON i18n
    - create_i18n_file: Fonction principale d'export

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-31
Version : 1.0
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime

from WebBridge_models import (
    I18nMeta, I18nTranslations, I18nEntry, SpacingMetadata
)
from WebBridge_utils import (
    parse_loc_line, find_file, find_files_by_pattern,
    load_json_file, save_json_file, get_language_from_filename,
    extract_prefix_from_loc_key, parse_extraction_timestamp,
    analyze_spacing
)


def load_translated_strings(filepath: str) -> Dict[str, Dict[str, str]]:
    """
    Charge un fichier TranslatedStrings_xx.txt.

    Args:
        filepath: Chemin du fichier TranslatedStrings_xx.txt

    Returns:
        Dictionnaire {loc_key: {prefix, category, key, value}}

    Example:
        >>> data = load_translated_strings("TranslatedStrings_en.txt")
        >>> data["$$$/Piwigo/API/AddTags"]
        {'prefix': '$$$/Piwigo', 'category': 'API', 'key': 'AddTags', 'value': 'to add tags'}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Fichier introuvable: {filepath}")

    result = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parsed = parse_loc_line(line)
            if parsed:
                # Créer la clé LOC complète
                loc_key = f"{parsed['prefix']}/{parsed['category']}/{parsed['key']}"
                result[loc_key] = parsed

    return result


def load_spacing_metadata_file(filepath: str) -> Dict[str, Dict]:
    """
    Charge le fichier spacing_metadata.json.

    Args:
        filepath: Chemin du fichier spacing_metadata.json

    Returns:
        Dictionnaire des métadonnées par clé LOC

    Example:
        >>> meta = load_spacing_metadata_file("spacing_metadata.json")
        >>> meta["$$$/Piwigo/API/CannotLogPiwigo"]["suffix"]
        ' -'
    """
    data = load_json_file(filepath)
    if not data:
        return {}

    # Retourner uniquement la section "metadata"
    return data.get("metadata", {})


def load_extraction_context(filepath: str) -> Dict[str, str]:
    """
    Charge le contexte d'extraction depuis extraction_report.txt.

    Extrait le contexte (fichier:ligne) pour chaque clé LOC.

    Args:
        filepath: Chemin du fichier extraction_report.txt

    Returns:
        Dictionnaire {loc_key: "fichier:ligne"}

    Example:
        >>> context = load_extraction_context("extraction_report.txt")
        >>> context["$$$/Piwigo/API/AddTags"]
        'PiwigoAPI.lua:145'
    """
    if not os.path.exists(filepath):
        return {}

    result = {}
    current_file = None

    # Pattern pour détecter le nom de fichier
    file_pattern = re.compile(r'^Fichier: (.+\.lua)$')
    # Pattern pour détecter une ligne de clé LOC avec numéro de ligne
    key_pattern = re.compile(r'^\s+\[Ligne (\d+)\]')
    loc_key_pattern = re.compile(r'CLÉ\s+: (\$\$\$/[^\s]+)')

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Détecter le fichier courant
        file_match = file_pattern.match(line)
        if file_match:
            current_file = file_match.group(1)
            i += 1
            continue

        # Détecter une ligne avec numéro de ligne
        key_match = key_pattern.match(lines[i])
        if key_match and current_file:
            line_num = key_match.group(1)

            # Chercher la clé LOC dans les lignes suivantes (généralement 2-3 lignes plus loin)
            for j in range(i, min(i + 5, len(lines))):
                loc_match = loc_key_pattern.search(lines[j])
                if loc_match:
                    loc_key = loc_match.group(1)
                    result[loc_key] = f"{current_file}:{line_num}"
                    break

        i += 1

    return result


def extract_categories_from_keys(loc_keys: List[str]) -> Dict[str, Set[str]]:
    """
    Extrait les catégories et clés depuis une liste de clés LOC.

    Args:
        loc_keys: Liste de clés LOC (ex: ["$$$/Piwigo/API/AddTags", ...])

    Returns:
        Dictionnaire {category: {key1, key2, ...}}

    Example:
        >>> extract_categories_from_keys(["$$$/Piwigo/API/AddTags", "$$$/Piwigo/API/Cancel"])
        {'API': {'AddTags', 'Cancel'}}
    """
    categories = {}

    for loc_key in loc_keys:
        # Format: $$$/Prefix/Category/Key
        parts = loc_key.split('/')
        if len(parts) >= 4:
            category = parts[2]
            key = parts[3]

            if category not in categories:
                categories[category] = set()
            categories[category].add(key)

    return categories


def export_to_i18n(
    extraction_dir: str,
    output_file: Optional[str] = None,
    plugin_name: str = "",
    include_languages: Optional[List[str]] = None
) -> Tuple[I18nTranslations, Dict[str, any]]:
    """
    Exporte les fichiers d'extraction vers le format JSON i18n.

    Args:
        extraction_dir: Dossier d'extraction (ex: __i18n_tmp__/Extractor/20260130_223727/)
        output_file: Fichier de sortie optionnel (si None, ne sauvegarde pas)
        plugin_name: Nom du plugin (ex: "piwigoPublish.lrplugin")
        include_languages: Langues à inclure (si None, toutes les langues trouvées)

    Returns:
        Tuple (I18nTranslations, stats)
        - I18nTranslations: Structure complète
        - stats: Statistiques d'export

    Raises:
        FileNotFoundError: Si TranslatedStrings_en.txt est manquant
        ValueError: Si le dossier d'extraction est invalide
    """
    if not os.path.exists(extraction_dir):
        raise ValueError(f"Dossier d'extraction introuvable: {extraction_dir}")

    # 1. Charger le fichier EN (obligatoire)
    en_file = find_file(extraction_dir, "TranslatedStrings_en.txt")
    if not en_file:
        raise FileNotFoundError(
            f"TranslatedStrings_en.txt manquant dans {extraction_dir}"
        )

    en_strings = load_translated_strings(en_file)

    # 2. Charger les métadonnées optionnelles
    spacing_file = find_file(extraction_dir, "spacing_metadata.json")
    spacing_meta = {}
    if spacing_file:
        spacing_meta = load_spacing_metadata_file(spacing_file)

    context_file = find_file(extraction_dir, "extraction_report.txt")
    context_data = {}
    if context_file:
        context_data = load_extraction_context(context_file)

    # 3. Détecter le préfixe et le plugin name si non fourni
    if en_strings:
        first_key = next(iter(en_strings.keys()))
        prefix = extract_prefix_from_loc_key(first_key) or "$$$/Unknown"
    else:
        prefix = "$$$/Unknown"

    if not plugin_name and extraction_dir:
        # Essayer de détecter depuis le chemin
        if ".lrplugin" in extraction_dir:
            parts = extraction_dir.split(os.sep)
            for part in parts:
                if part.endswith(".lrplugin"):
                    plugin_name = part
                    break

    # 4. Détecter les autres langues disponibles
    all_translation_files = find_files_by_pattern(
        extraction_dir, "TranslatedStrings_*.txt", recursive=False
    )

    available_languages = set()
    for filepath in all_translation_files:
        lang = get_language_from_filename(os.path.basename(filepath))
        if lang:
            available_languages.add(lang)

    # Filtrer selon include_languages si spécifié
    if include_languages:
        languages = [lang for lang in include_languages if lang in available_languages]
    else:
        languages = sorted(available_languages)

    # 5. Créer les métadonnées
    timestamp_str = parse_extraction_timestamp(extraction_dir) or "unknown"
    source_extraction = f"Extractor/{timestamp_str}"

    meta = I18nMeta(
        version="1.0",
        plugin_name=plugin_name,
        prefix=prefix,
        source_extraction=source_extraction,
        total_keys=len(en_strings),
        languages=languages,
        webbridge_version="1.0.0"
    )

    # 6. Créer la structure i18n
    translations = I18nTranslations(meta=meta)

    # 7. Traiter chaque langue
    stats = {
        "total_keys": len(en_strings),
        "languages_processed": [],
        "keys_with_metadata": 0,
        "keys_with_context": 0,
        "warnings": []
    }

    for lang in languages:
        # Charger le fichier de langue
        if lang == "en":
            lang_strings = en_strings
        else:
            lang_file = find_file(extraction_dir, f"TranslatedStrings_{lang}.txt")
            if not lang_file:
                stats["warnings"].append(f"Fichier TranslatedStrings_{lang}.txt introuvable")
                continue
            lang_strings = load_translated_strings(lang_file)

        # Ajouter les entrées
        for loc_key, data in en_strings.items():
            category = data['category']
            key = data['key']

            # Récupérer la valeur traduite (ou EN par défaut)
            if lang == "en":
                value = data['value']
            else:
                value = lang_strings.get(loc_key, {}).get('value', data['value'])

            # Créer l'entrée
            entry = I18nEntry(text=value)

            # Ajouter le contexte (uniquement pour EN)
            if lang == "en" and loc_key in context_data:
                entry.context = context_data[loc_key]
                stats["keys_with_context"] += 1

            # Ajouter la chaîne de référence (EN) pour toutes les langues
            # Pour EN: inclure la valeur comme référence de base
            # Pour autres langues: permet aux traducteurs de voir le texte original pendant l'édition
            entry.default = data['value']

            # NOTE: Les métadonnées d'espacement NE SONT PAS exportées
            # Elles sont utiles uniquement pour la reconstruction du code source Lua,
            # pas pour les fichiers TranslatedStrings_xx.txt qui sont déjà nettoyés.
            # Le cycle export → import doit préserver les fichiers .txt tels quels.

            translations.add_entry(lang, category, key, entry)

        stats["languages_processed"].append(lang)

    # 8. Sauvegarder si output_file spécifié
    if output_file:
        json_data = translations.to_dict()
        if save_json_file(output_file, json_data, indent=2):
            stats["output_file"] = output_file
        else:
            stats["warnings"].append(f"Échec de sauvegarde vers {output_file}")

    return translations, stats


def create_i18n_file(
    plugin_path: str,
    output_file: Optional[str] = None,
    extraction_timestamp: Optional[str] = None,
    languages: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Fonction principale pour créer un fichier i18n depuis un plugin.

    Args:
        plugin_path: Chemin vers le plugin .lrplugin
        output_file: Fichier de sortie (si None, auto-généré)
        extraction_timestamp: Timestamp d'extraction spécifique (si None, prend le dernier)
        languages: Langues à inclure (si None, toutes)

    Returns:
        Statistiques d'export

    Example:
        >>> stats = create_i18n_file(
        ...     "/path/to/plugin.lrplugin",
        ...     "i18n_translations.json"
        ... )
        >>> print(f"Exporté {stats['total_keys']} clés")
    """
    from common.paths import get_i18n_kit_path, find_latest_tool_output

    # Trouver le dossier d'extraction
    if extraction_timestamp:
        extraction_dir = os.path.join(
            get_i18n_kit_path(plugin_path),
            "Extractor",
            extraction_timestamp
        )
    else:
        extraction_dir = find_latest_tool_output(plugin_path, "Extractor")

    if not extraction_dir or not os.path.exists(extraction_dir):
        raise ValueError(
            f"Aucun dossier d'extraction trouvé pour {plugin_path}\n"
            f"Veuillez exécuter l'Extractor d'abord."
        )

    # Générer le nom de fichier de sortie si non spécifié
    if not output_file:
        plugin_name = os.path.basename(plugin_path)
        output_file = os.path.join(
            extraction_dir,
            f"{plugin_name}_i18n.json"
        )

    # Extraire le nom du plugin
    plugin_name = os.path.basename(plugin_path)

    # Exporter
    translations, stats = export_to_i18n(
        extraction_dir,
        output_file,
        plugin_name,
        languages
    )

    return stats


if __name__ == "__main__":
    # Test rapide
    import sys

    if len(sys.argv) > 1:
        plugin_path = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None

        try:
            stats = create_i18n_file(plugin_path, output_file)
            print(f"✓ Export réussi:")
            print(f"  - Clés exportées: {stats['total_keys']}")
            print(f"  - Langues: {', '.join(stats['languages_processed'])}")
            print(f"  - Clés avec métadonnées: {stats['keys_with_metadata']}")
            print(f"  - Clés avec contexte: {stats['keys_with_context']}")
            if 'output_file' in stats:
                print(f"  - Fichier: {stats['output_file']}")
        except Exception as e:
            print(f"✗ Erreur: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python WebBridge_export.py <plugin_path> [output_file]")
        sys.exit(1)
