#!/usr/bin/env python3
"""
Extractor_main.py

Script d'extraction des chaînes localisables pour plugins Adobe Lightroom Classic.
Analyse les fichiers Lua et extrait toutes les chaînes hardcodées qui devraient
être localisées via le système LOC "$$$/.../".

Basé sur le skill: lightroom-localization-extraction

Usage (CLI):
    python Extractor_main.py --plugin-path /path/to/plugin.lrplugin [options]

Usage (Menu interactif):
    python Extractor_main.py

Options (CLI):
    --plugin-path PATH    Chemin vers le plugin (OBLIGATOIRE)
    --output-dir PATH     Override répertoire de sortie (défaut: __i18n_kit__/)
    --prefix PREFIX       Préfixe des clés LOC (défaut: $$$/Piwigo)
    --lang LANG           Code langue (défaut: en)
    --exclude FILE        Fichiers à exclure (répétable)
    --min-length N        Longueur minimale des chaînes (défaut: 3)
    --no-ignore-log       NE PAS ignorer les lignes de log

Les fichiers sont générés dans: <plugin>/__i18n_kit__/1_Extractor/<timestamp>/

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-27
Version : 5.1 - Avec menu interactif et centralisation des outputs
"""

import os
import sys
import argparse
from datetime import datetime

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import get_tool_output_path

from Extractor_engine import LocalizableStringExtractor
from Extractor_output import OutputGenerator
from Extractor_report import ReportGenerator
from Extractor_menu import show_interactive_menu


def run_extraction(plugin_path: str, output_dir: str, prefix: str, lang: str,
                   exclude_files: list, min_length: int, ignore_log: bool):
    """Lance l'extraction avec les paramètres fournis."""
    
    # Vérifier le chemin du plugin
    if not os.path.isdir(plugin_path):
        print(f"❌ ERREUR: Répertoire introuvable: {plugin_path}")
        sys.exit(1)

    # Déterminer le répertoire de sortie
    # Nouvelle structure: <plugin>/__i18n_kit__/1_Extractor/<timestamp>/
    if output_dir:
        # Override manuel (rétrocompatibilité)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamped_output_dir = os.path.join(output_dir, timestamp)
        os.makedirs(timestamped_output_dir, exist_ok=True)
    else:
        # Nouvelle structure dans le plugin
        timestamped_output_dir = get_tool_output_path(plugin_path, "Extractor", create=True)
    
    print(f"\n{'=' * 80}")
    print(f"EXTRACTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}")
    print(f"Plugin: {plugin_path}")
    print(f"Sortie: {timestamped_output_dir}")
    print(f"Préfixe: {prefix}")
    print(f"Langue: {lang}")
    print(f"{'=' * 80}\n")
    
    # Créer l'extracteur
    extractor = LocalizableStringExtractor(
        plugin_path=plugin_path,
        prefix=prefix,
        min_length=min_length,
        exclude_files=exclude_files,
        ignore_log=ignore_log
    )
    
    # Extraire
    print(f"Analyse de {plugin_path}...")
    extractor.extract_all()
    
    # Chemins des fichiers de sortie dans le sous-dossier timestampé
    strings_file = os.path.join(timestamped_output_dir, f"TranslatedStrings_{lang}.txt")
    spacing_file = os.path.join(timestamped_output_dir, "spacing_metadata.json")
    replacements_file = os.path.join(timestamped_output_dir, "replacements.json")
    report_file = os.path.join(timestamped_output_dir, f"extraction_report.txt")
    
    # Générateurs
    output_gen = OutputGenerator(plugin_path, prefix)
    report_gen = ReportGenerator(plugin_path, prefix, extractor.stats)
    
    # Générer les fichiers
    output_gen.generate_plugin_strings(extractor.extracted, strings_file, lang)
    output_gen.generate_spacing_metadata(extractor.spacing_metadata, extractor.text_to_key, spacing_file)
    output_gen.generate_replacements_json(extractor.extracted, replacements_file, extractor.text_to_key)
    report_gen.generate_report(extractor.extracted, extractor.spacing_metadata, report_file)
    
    # Afficher le résumé
    extractor.print_summary()
    
    print(f"\n{'=' * 80}")
    print("FICHIERS GÉNÉRÉS")
    print(f"{'=' * 80}")
    print(f"📂 Dossier de sortie: {timestamped_output_dir}")
    print(f"\n📄 Fichiers créés:")
    print(f"  ✓ TranslatedStrings_{lang}.txt ({extractor.stats.unique_strings} clés)")
    print(f"  ✓ spacing_metadata.json ({len(extractor.spacing_metadata)} entrées)")
    print(f"  ✓ replacements.json (pour Applicator)")
    print(f"  ✓ extraction_report.txt (rapport détaillé)")
    print(f"{'=' * 80}\n")


def main():
    """Point d'entree principal."""

    # Verifier si mode interactif (aucun argument ou seulement --default-plugin)
    if len(sys.argv) == 1 or (len(sys.argv) == 3 and sys.argv[1] == '--default-plugin'):
        # Recuperer le chemin par defaut si fourni
        default_plugin = ""
        if len(sys.argv) == 3 and sys.argv[1] == '--default-plugin':
            default_plugin = sys.argv[2]

        # Menu interactif avec plugin pre-configure
        result = show_interactive_menu(default_plugin)

        if result is None:
            print("\nExtraction annulee")
            sys.exit(1)

        plugin_path, output_dir, prefix, lang, exclude_files, min_length, ignore_log = result

        run_extraction(
            plugin_path=plugin_path,
            output_dir=output_dir,
            prefix=prefix,
            lang=lang,
            exclude_files=exclude_files,
            min_length=min_length,
            ignore_log=ignore_log
        )
    else:
        # Arguments en ligne de commande
        parser = argparse.ArgumentParser(
            description="Extrait les chaînes localisables d'un plugin Lightroom Classic",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemples:
  # Mode interactif (menu)
  python Extractor_main.py
  
  # Mode CLI
  python Extractor_main.py --plugin-path ./piwigoPublish.lrplugin
  python Extractor_main.py --plugin-path ./plugin --output-dir ./output
            """
        )
        
        parser.add_argument('--plugin-path', required=True,
                            help='Chemin vers le répertoire du plugin (OBLIGATOIRE)')
        parser.add_argument('--output-dir', default=None,
                            help='Override répertoire de sortie (défaut: <plugin>/__i18n_kit__/1_Extractor/)')
        parser.add_argument('--prefix', default='$$$/Piwigo',
                            help='Préfixe des clés LOC (défaut: $$$/Piwigo)')
        parser.add_argument('--lang', default='en',
                            help='Code langue (défaut: en)')
        parser.add_argument('--exclude', action='append', default=[],
                            help='Fichiers à exclure (répétable)')
        parser.add_argument('--min-length', type=int, default=3,
                            help='Longueur minimale des chaînes (défaut: 3)')
        parser.add_argument('--no-ignore-log', action='store_true',
                            help='NE PAS ignorer les lignes de log')
        
        args = parser.parse_args()
        
        run_extraction(
            plugin_path=args.plugin_path,
            output_dir=args.output_dir or "",
            prefix=args.prefix,
            lang=args.lang,
            exclude_files=args.exclude,
            min_length=args.min_length,
            ignore_log=not args.no_ignore_log
        )


if __name__ == "__main__":
    main()
