#!/usr/bin/env python3
"""
WebBridge_import.py

Import du fichier JSON i18n vers le format Lightroom SDK (TranslatedStrings_xx.txt).

Fonctions principales:
    - generate_file_header: Génère l'en-tête du fichier .txt
    - reconstruct_translated_strings: Reconstruit un fichier TranslatedStrings_xx.txt
    - import_from_i18n: Fonction principale d'import
    - create_translated_strings_files: Crée tous les fichiers TranslatedStrings

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-31
Version : 1.0
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from WebBridge_models import I18nTranslations, I18nEntry
from WebBridge_utils import (
    build_loc_line, load_json_file, save_json_file
)
from WebBridge_validator import validate_i18n_file


TRANSLATOR_NOTES = """-- -----------------------------------------------------------------------------
-- IMPORTANT NOTES FOR TRANSLATORS:
-- -----------------------------------------------------------------------------
-- 1. DO NOT translate the following patterns:
--    - Format specifiers: %s, %d, %f, %u, %x, %X, %o, %c, %e, %E, %g, %G
--    - Escape sequences: \\n (newline), \\t (tab), \\" (quote), \\\\ (backslash)
--
-- 2. PRESERVE the number and order of format specifiers:
--    EN: "Created %d albums, updated %d"
--    FR: "Créé %d albums, mis à jour %d"  (CORRECT - same placeholders)
--    FR: "Créé %s albums"                 (WRONG - missing second %d)
--
-- 3. PRESERVE intentional spaces around text:
--    - Leading spaces indicate alignment requirements
--    - Trailing spaces or suffixes (: - ...) are intentional
--
-- 4. Context information (file:line) helps understand where the text is used
--    - Check the original source code if meaning is unclear
--
-- 5. DO NOT modify or remove LOC keys (the part before '=')
--    - Only translate the text after '='
-- -----------------------------------------------------------------------------
"""


def generate_file_header(
    language: str,
    total_keys: int,
    plugin_name: str = "",
    source_file: str = ""
) -> str:
    """
    Génère l'en-tête d'un fichier TranslatedStrings_xx.txt.

    Args:
        language: Code langue (ex: "fr", "de")
        total_keys: Nombre total de clés
        plugin_name: Nom du plugin optionnel
        source_file: Fichier source JSON optionnel

    Returns:
        Texte de l'en-tête

    Example:
        >>> header = generate_file_header("fr", 272, "piwigoPublish.lrplugin")
        >>> print(header)
        -- =============================================================================
        -- Plugin Localization - FR
        ...
    """
    lang_upper = language.upper()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    header = f"""-- =============================================================================
-- Plugin Localization - {lang_upper}
-- Generated: {now}
-- Total keys: {total_keys}"""

    if plugin_name:
        header += f"\n-- Plugin: {plugin_name}"

    if source_file:
        header += f"\n-- Source: {source_file}"

    header += "\n-- ============================================================================="
    header += "\n"
    header += TRANSLATOR_NOTES

    return header


def reconstruct_translated_strings(
    translations: I18nTranslations,
    language: str,
    output_file: Optional[str] = None,
    include_header: bool = True
) -> Tuple[str, Dict[str, any]]:
    """
    Reconstruit un fichier TranslatedStrings_xx.txt depuis I18nTranslations.

    Args:
        translations: Objet I18nTranslations
        language: Code langue à exporter (ex: "fr", "de")
        output_file: Fichier de sortie optionnel (si None, retourne juste le contenu)
        include_header: Inclure l'en-tête du fichier (défaut: True)

    Returns:
        Tuple (content, stats)
        - content: Contenu du fichier TranslatedStrings_xx.txt
        - stats: Statistiques de reconstruction

    Raises:
        ValueError: Si la langue n'existe pas dans translations
    """
    if language not in translations.translations:
        raise ValueError(f"Langue '{language}' introuvable dans les traductions")

    # Récupérer les traductions pour cette langue
    lang_trans = translations.translations[language]

    # Récupérer les traductions EN comme référence (pour l'ordre et les métadonnées)
    en_trans = translations.translations.get("en", {})

    prefix = translations.meta.prefix

    # Statistiques
    stats = {
        "language": language,
        "total_keys": 0,
        "keys_with_metadata": 0,
        "fallback_to_en": 0,
        "warnings": []
    }

    # Construire le contenu
    lines = []

    if include_header:
        header = generate_file_header(
            language,
            translations.meta.total_keys,
            translations.meta.plugin_name,
            "i18n JSON"
        )
        lines.append(header)

    # Parcourir les catégories dans l'ordre alphabétique
    for category in sorted(en_trans.keys()):
        # Ajouter séparateur de catégorie
        lines.append(f"\n-- {category}")

        # Parcourir les clés de cette catégorie dans l'ordre alphabétique
        category_keys = en_trans.get(category, {})
        for key in sorted(category_keys.keys()):
            # Récupérer l'entrée pour cette langue (ou fallback vers EN)
            entry = None
            fallback = False

            if category in lang_trans and key in lang_trans[category]:
                entry = lang_trans[category][key]
            elif language != "en" and category in en_trans and key in en_trans[category]:
                # Fallback vers EN si traduction manquante
                entry = en_trans[category][key]
                fallback = True
                stats["fallback_to_en"] += 1
                stats["warnings"].append(f"{category}.{key}: Utilise EN par défaut")

            if not entry:
                stats["warnings"].append(f"{category}.{key}: Introuvable")
                continue

            # NOTE: Les métadonnées d'espacement ne sont PAS réappliquées
            # Les fichiers TranslatedStrings_xx.txt doivent rester nettoyés (sans espaces intentionnels)
            # Les métadonnées sont utiles uniquement pour reconstruire le code source Lua

            # Récupérer le texte
            if isinstance(entry, I18nEntry):
                text = entry.text
            else:
                text = entry.get("text", "")

            # Construire la ligne SANS métadonnées (pas de réapplication d'espaces)
            line = build_loc_line(prefix, category, key, text, None)
            lines.append(line)

            stats["total_keys"] += 1

    # Joindre toutes les lignes
    content = "\n".join(lines)

    # Sauvegarder si output_file spécifié
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        stats["output_file"] = output_file

    return content, stats


def import_from_i18n(
    json_file: str,
    output_dir: str,
    languages: Optional[List[str]] = None,
    validate: bool = True
) -> Dict[str, any]:
    """
    Importe un fichier JSON i18n et crée les fichiers TranslatedStrings_xx.txt.

    Args:
        json_file: Chemin du fichier JSON i18n
        output_dir: Dossier de sortie pour les fichiers .txt
        languages: Langues à exporter (si None, toutes les langues du JSON)
        validate: Valider le JSON avant import (défaut: True)

    Returns:
        Dictionnaire de statistiques globales

    Raises:
        FileNotFoundError: Si le fichier JSON n'existe pas
        ValueError: Si la validation échoue

    Example:
        >>> stats = import_from_i18n(
        ...     "translations.json",
        ...     "/path/to/output",
        ...     languages=["en", "fr"]
        ... )
        >>> print(f"Créé {stats['files_created']} fichiers")
    """
    if not os.path.exists(json_file):
        raise FileNotFoundError(f"Fichier JSON introuvable: {json_file}")

    # Créer le dossier de sortie si nécessaire
    os.makedirs(output_dir, exist_ok=True)

    # Charger le JSON
    data = load_json_file(json_file)
    if not data:
        raise ValueError(f"Impossible de charger le fichier JSON: {json_file}")

    # Valider si demandé
    if validate:
        result = validate_i18n_file(data=data)
        if not result.is_valid():
            error_messages = [str(e) for e in result.errors]
            raise ValueError(
                f"Validation du JSON échouée:\n" + "\n".join(error_messages)
            )

    # Charger dans I18nTranslations
    translations = I18nTranslations.from_dict(data)

    # Déterminer les langues à exporter
    if languages is None:
        languages = list(translations.translations.keys())
    else:
        # Vérifier que les langues demandées existent
        available = set(translations.translations.keys())
        requested = set(languages)
        missing = requested - available
        if missing:
            raise ValueError(f"Langues manquantes dans le JSON: {', '.join(missing)}")

    # Statistiques globales
    global_stats = {
        "json_file": json_file,
        "output_dir": output_dir,
        "languages_processed": [],
        "files_created": 0,
        "total_keys": 0,
        "total_fallbacks": 0,
        "warnings": [],
        "language_stats": {}
    }

    # Exporter chaque langue
    for lang in languages:
        output_file = os.path.join(output_dir, f"TranslatedStrings_{lang}.txt")

        try:
            content, stats = reconstruct_translated_strings(
                translations,
                lang,
                output_file,
                include_header=True
            )

            global_stats["languages_processed"].append(lang)
            global_stats["files_created"] += 1
            global_stats["total_keys"] += stats["total_keys"]
            global_stats["total_fallbacks"] += stats["fallback_to_en"]
            global_stats["language_stats"][lang] = stats

            if stats["warnings"]:
                global_stats["warnings"].extend([f"[{lang}] {w}" for w in stats["warnings"]])

        except Exception as e:
            global_stats["warnings"].append(f"[{lang}] Erreur: {e}")

    return global_stats


def create_translated_strings_files(
    json_file: str,
    plugin_path: str,
    languages: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Fonction principale pour créer les fichiers TranslatedStrings depuis JSON.

    Args:
        json_file: Chemin du fichier JSON i18n
        plugin_path: Chemin vers le plugin .lrplugin
        languages: Langues à exporter (si None, toutes)

    Returns:
        Statistiques d'import

    Example:
        >>> stats = create_translated_strings_files(
        ...     "translations.json",
        ...     "/path/to/plugin.lrplugin",
        ...     languages=["en", "fr", "de"]
        ... )
    """
    from common.paths import get_i18n_kit_path

    # Créer le dossier d'import dans __i18n_tmp__
    i18n_kit_path = get_i18n_kit_path(plugin_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(i18n_kit_path, "WebBridge", timestamp)

    # Importer
    stats = import_from_i18n(
        json_file,
        output_dir,
        languages,
        validate=True
    )

    return stats


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        json_file = sys.argv[1]
        output_dir = sys.argv[2]
        languages = sys.argv[3:] if len(sys.argv) > 3 else None

        try:
            stats = import_from_i18n(json_file, output_dir, languages)

            print(f"[OK] Import réussi!\n")
            print("STATISTIQUES:")
            print("-" * 80)
            print(f"  Fichiers créés            : {stats['files_created']}")
            print(f"  Langues traitées          : {', '.join(stats['languages_processed'])}")
            print(f"  Clés totales exportées    : {stats['total_keys']}")
            print(f"  Fallbacks vers EN         : {stats['total_fallbacks']}")

            if stats.get('warnings'):
                print(f"\n  Avertissements            : {len(stats['warnings'])}")
                for warning in stats['warnings'][:10]:  # Limiter à 10
                    print(f"    - {warning}")
                if len(stats['warnings']) > 10:
                    print(f"    ... et {len(stats['warnings']) - 10} autres")

            print(f"\n  Dossier de sortie         : {stats['output_dir']}")

        except Exception as e:
            print(f"\n[ERROR] ERREUR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("Usage: python WebBridge_import.py <json_file> <output_dir> [lang1 lang2 ...]")
        print("\nExemple:")
        print("  python WebBridge_import.py translations.json ./output en fr de")
        sys.exit(1)
