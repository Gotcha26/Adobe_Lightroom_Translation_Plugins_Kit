#!/usr/bin/env python3
"""
WebBridge_main.py

Script principal pour le WebBridge - export/import de traductions au format JSON i18n.
Permet l'échange de traductions avec des plateformes web tierces.

Usage (Menu interactif):
    python WebBridge_main.py

Usage (CLI):
    python WebBridge_main.py export --plugin-path /path/to/plugin [--output output.json]
    python WebBridge_main.py import --json translations.json --plugin-path /path/to/plugin [--languages en,fr]

Modes disponibles:
    - export: Exporte TranslatedStrings_xx.txt vers JSON i18n
    - import: Importe JSON i18n vers TranslatedStrings_xx.txt
    - validate: Valide un fichier JSON i18n
    - roundtrip: Test du cycle complet export → import → comparaison

Les fichiers sont générés dans: <plugin>/__i18n_kit__/4_WebBridge/<timestamp>/

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-31
Version : 1.0 - Phase 4 avec menu interactif
"""

import os
import sys
import argparse
from datetime import datetime
from typing import Optional, List, Dict

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import get_tool_output_path, find_latest_tool_output
from common.colors import Colors

# Imports WebBridge
from WebBridge_export import export_to_i18n
from WebBridge_import import import_from_i18n
from WebBridge_validator import validate_i18n_file
from WebBridge_menu import show_interactive_menu

# Instance couleurs
c = Colors()


def print_export_stats(stats: Dict):
    """Affiche les statistiques d'export."""
    print()
    print(c.title("STATISTIQUES D'EXPORT"))
    print(c.separator())
    print(c.config_line("Clés exportées", str(stats['total_keys'])))
    print(c.config_line("Langues", ', '.join(stats['languages_processed'])))
    print(c.config_line("Clés avec contexte", str(stats['keys_with_context'])))
    print(c.config_line("Clés avec métadonnées", str(stats['keys_with_metadata'])))

    if stats.get('warnings'):
        print()
        print(c.warning(f"{len(stats['warnings'])} avertissements"))
        for warn in stats['warnings'][:5]:
            print(f"  {c.DIM}- {warn}{c.RESET}")
        if len(stats['warnings']) > 5:
            print(f"  {c.DIM}... et {len(stats['warnings']) - 5} autres{c.RESET}")
    print()


def print_import_stats(stats: Dict):
    """Affiche les statistiques d'import."""
    print()
    print(c.title("STATISTIQUES D'IMPORT"))
    print(c.separator())
    print(c.config_line("Fichiers créés", str(stats['files_created'])))
    print(c.config_line("Langues traitées", ', '.join(stats['languages_processed'])))
    print(c.config_line("Clés importées", str(stats['total_keys'])))
    print(c.config_line("Fallbacks vers EN", str(stats['total_fallbacks'])))

    if stats.get('warnings'):
        print()
        print(c.warning(f"{len(stats['warnings'])} avertissements"))
        for warn in stats['warnings'][:5]:
            print(f"  {c.DIM}- {warn}{c.RESET}")
        if len(stats['warnings']) > 5:
            print(f"  {c.DIM}... et {len(stats['warnings']) - 5} autres{c.RESET}")
    print()


def print_validation_result(result):
    """Affiche le résultat de validation."""
    print()
    print(c.title("RÉSULTAT DE VALIDATION"))
    print(c.separator())

    if result.is_valid():
        print(c.success("Fichier JSON valide!"))
        print(c.config_line("Erreurs", "0"))
        print(c.config_line("Avertissements", str(result.warning_count())))
    else:
        print(c.error("Fichier JSON invalide!"))
        print(c.config_line("Erreurs", str(result.error_count()), key_width=20))
        print(c.config_line("Avertissements", str(result.warning_count()), key_width=20))

    print()

    # Afficher les erreurs
    if result.errors:
        print(c.error(f"{len(result.errors)} erreur(s) trouvée(s):"))
        for err in result.errors[:10]:
            print(f"  {c.ERROR}[{err.category}]{c.RESET} {err.message}")
            if err.details:
                for key, value in list(err.details.items())[:3]:
                    print(f"    {c.DIM}{key}: {value}{c.RESET}")
        if len(result.errors) > 10:
            print(f"  {c.DIM}... et {len(result.errors) - 10} autres erreurs{c.RESET}")
        print()

    # Afficher les warnings
    if result.warnings:
        print(c.warning(f"{len(result.warnings)} avertissement(s):"))
        for warn in result.warnings[:10]:
            print(f"  {c.WARNING}[{warn.category}]{c.RESET} {warn.message}")
        if len(result.warnings) > 10:
            print(f"  {c.DIM}... et {len(result.warnings) - 10} autres avertissements{c.RESET}")
        print()


def run_export(plugin_path: str, extraction_dir: Optional[str] = None,
               output_file: Optional[str] = None, plugin_name: Optional[str] = None):
    """Lance l'export vers JSON i18n."""

    # Vérifier le chemin du plugin
    if not os.path.isdir(plugin_path):
        print(c.error(f"Répertoire introuvable: {plugin_path}"))
        sys.exit(1)

    # Auto-détection du dossier d'extraction si non spécifié
    if not extraction_dir:
        extraction_dir = find_latest_tool_output(plugin_path, "Extractor")
        if not extraction_dir:
            print(c.error("Aucune extraction trouvée dans __i18n_kit__/Extractor/"))
            print("        Lancez d'abord Extractor sur ce plugin.")
            sys.exit(1)
        print(c.info(f"Auto-détection: {extraction_dir}"))

    if not os.path.isdir(extraction_dir):
        print(c.error(f"Répertoire Extractor introuvable: {extraction_dir}"))
        sys.exit(1)

    # Déterminer le fichier de sortie
    if not output_file:
        webbridge_output = get_tool_output_path(plugin_path, "WebBridge", create=True)
        output_file = os.path.join(webbridge_output, "translations.json")

    # Déterminer le nom du plugin
    if not plugin_name:
        plugin_name = os.path.basename(plugin_path)

    print()
    print(c.box_header("WEBBRIDGE - EXPORT VERS JSON i18n"))
    print()
    print(c.config_line("Plugin", plugin_path))
    print(c.config_line("Dossier Extractor", extraction_dir))
    print(c.config_line("Fichier JSON", output_file))
    print(c.config_line("Nom du plugin", plugin_name))
    print()
    print(c.separator())
    print()

    # Exporter
    try:
        translations, stats = export_to_i18n(
            extraction_dir,
            output_file=output_file,
            plugin_name=plugin_name
        )

        print(c.success(f"Export réussi!"))
        print_export_stats(stats)
        print(c.config_line("Fichier créé", output_file))
        print()

        return True

    except Exception as e:
        print(c.error(f"Erreur lors de l'export: {e}"))
        import traceback
        traceback.print_exc()
        return False


def run_import(json_file: str, plugin_path: str,
               languages: Optional[List[str]] = None, validate: bool = True):
    """Lance l'import depuis JSON i18n."""

    # Vérifier le fichier JSON
    if not os.path.exists(json_file):
        print(c.error(f"Fichier JSON introuvable: {json_file}"))
        sys.exit(1)

    # Vérifier le chemin du plugin
    if not os.path.isdir(plugin_path):
        print(c.error(f"Répertoire introuvable: {plugin_path}"))
        sys.exit(1)

    # Créer le dossier de sortie WebBridge
    webbridge_output = get_tool_output_path(plugin_path, "WebBridge", create=True)

    print()
    print(c.box_header("WEBBRIDGE - IMPORT DEPUIS JSON i18n"))
    print()
    print(c.config_line("Fichier JSON", json_file))
    print(c.config_line("Plugin", plugin_path))
    print(c.config_line("Dossier de sortie", webbridge_output))
    if languages:
        print(c.config_line("Langues", ', '.join(languages)))
    else:
        print(c.config_line("Langues", "Toutes"))
    print(c.config_line("Validation", "Oui" if validate else "Non"))
    print()
    print(c.separator())
    print()

    # Importer
    try:
        stats = import_from_i18n(
            json_file,
            webbridge_output,
            languages=languages,
            validate=validate
        )

        print(c.success("Import réussi!"))
        print_import_stats(stats)
        print()
        print(c.info("Fichiers créés dans:"))
        print(f"  {c.VALUE}{webbridge_output}{c.RESET}")
        print()

        return True

    except Exception as e:
        print(c.error(f"Erreur lors de l'import: {e}"))
        import traceback
        traceback.print_exc()
        return False


def run_validate(json_file: str):
    """Valide un fichier JSON i18n."""

    # Vérifier le fichier JSON
    if not os.path.exists(json_file):
        print(c.error(f"Fichier JSON introuvable: {json_file}"))
        sys.exit(1)

    print()
    print(c.box_header("WEBBRIDGE - VALIDATION JSON i18n"))
    print()
    print(c.config_line("Fichier JSON", json_file))
    print()
    print(c.separator())

    # Valider
    try:
        result = validate_i18n_file(json_file)
        print_validation_result(result)

        return result.is_valid()

    except Exception as e:
        print(c.error(f"Erreur lors de la validation: {e}"))
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée principal."""

    # Mode interactif si aucun argument ou seulement --default-plugin
    if len(sys.argv) == 1 or (len(sys.argv) == 3 and sys.argv[1] == '--default-plugin'):
        # Récupérer le chemin par défaut si fourni
        default_plugin = ""
        if len(sys.argv) == 3 and sys.argv[1] == '--default-plugin':
            default_plugin = sys.argv[2]

        # Menu interactif avec plugin pré-configuré
        result = show_interactive_menu(default_plugin)

        if result is None:
            print("\nOpération annulée")
            sys.exit(1)

        mode, params = result

        if mode == 'export':
            success = run_export(**params)
        elif mode == 'import':
            success = run_import(**params)
        elif mode == 'validate':
            success = run_validate(**params)
        else:
            print(c.error(f"Mode inconnu: {mode}"))
            sys.exit(1)

        sys.exit(0 if success else 1)

    # Mode CLI
    parser = argparse.ArgumentParser(
        description="WebBridge - Export/Import de traductions au format JSON i18n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:

  # Mode interactif (menu)
  python WebBridge_main.py

  # Export vers JSON
  python WebBridge_main.py export --plugin-path ./plugin.lrplugin
  python WebBridge_main.py export --plugin-path ./plugin --output traductions.json

  # Import depuis JSON
  python WebBridge_main.py import --json traductions.json --plugin-path ./plugin
  python WebBridge_main.py import --json tr.json --plugin-path ./plugin --languages en,fr

  # Validation JSON
  python WebBridge_main.py validate --json traductions.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Mode à utiliser')

    # Export
    export_parser = subparsers.add_parser('export', help='Exporter vers JSON i18n')
    export_parser.add_argument('--plugin-path', required=True,
                              help='Chemin vers le répertoire du plugin (OBLIGATOIRE)')
    export_parser.add_argument('--extraction-dir', default=None,
                              help='Répertoire Extractor (défaut: auto-détection __i18n_kit__/Extractor/)')
    export_parser.add_argument('--output', default=None,
                              help='Fichier JSON de sortie (défaut: <plugin>/__i18n_kit__/WebBridge/<timestamp>/translations.json)')
    export_parser.add_argument('--plugin-name', default=None,
                              help='Nom du plugin (défaut: nom du répertoire)')

    # Import
    import_parser = subparsers.add_parser('import', help='Importer depuis JSON i18n')
    import_parser.add_argument('--json', required=True,
                              help='Fichier JSON i18n à importer (OBLIGATOIRE)')
    import_parser.add_argument('--plugin-path', required=True,
                              help='Chemin vers le répertoire du plugin (OBLIGATOIRE)')
    import_parser.add_argument('--languages', default=None,
                              help='Langues à importer (ex: en,fr,de) (défaut: toutes)')
    import_parser.add_argument('--no-validate', action='store_true',
                              help='Ne pas valider avant import')

    # Validate
    validate_parser = subparsers.add_parser('validate', help='Valider un fichier JSON i18n')
    validate_parser.add_argument('--json', required=True,
                                help='Fichier JSON i18n à valider (OBLIGATOIRE)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Exécuter la commande
    if args.command == 'export':
        success = run_export(
            plugin_path=args.plugin_path,
            extraction_dir=args.extraction_dir,
            output_file=args.output,
            plugin_name=args.plugin_name
        )
    elif args.command == 'import':
        languages = args.languages.split(',') if args.languages else None
        success = run_import(
            json_file=args.json,
            plugin_path=args.plugin_path,
            languages=languages,
            validate=not args.no_validate
        )
    elif args.command == 'validate':
        success = run_validate(json_file=args.json)
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
