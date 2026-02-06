#!/usr/bin/env python3
"""
Nom du fichier : main.py

Dépendances : .engine, .output, .report, .menu

Description :
Point d'entrée principal pour l'extraction des chaînes localisables d'un plugin Adobe Lightroom Classic.
Gère le mode CLI et le mode menu interactif. Lance l'extracteur, génère les fichiers de sortie et les rapports.

Usage CLI :
    python -m tools.extractor.main --plugin-path /path/to/plugin.lrplugin [options]

    Options:
        --plugin-path PATH    Chemin du plugin (OBLIGATOIRE)
        --output-dir PATH     Override du répertoire de sortie
        --prefix PREFIX       Préfixe LOC (défaut: $$$/Piwigo)
        --lang LANG           Code langue (défaut: en)
        --exclude FILE        Fichiers à exclure (répétable)
        --min-length N        Longueur minimale (défaut: 3)
        --no-ignore-log       NE PAS ignorer les logs

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import argparse
from datetime import datetime

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.paths import get_tool_output_path
from core.output_formatters import OutputFormatter
from core.i18n import _

from .engine import LocalizableStringExtractor
from .output import OutputGenerator
from .report import ReportGenerator
from .menu import show_interactive_menu


def run_extraction(plugin_path: str, output_dir: str, prefix: str, lang: str,
                   exclude_files: list, min_length: int, ignore_log: bool, silent: bool = False):
    """Lance l'extraction avec les paramètres fournis.

    Args:
        silent: Si True, supprime tous les affichages (pour utilisation dans AUTO-SYNC)
    """

    # Vérifier le chemin du plugin
    if not os.path.isdir(plugin_path):
        print(_("ERREUR: Répertoire introuvable: {path}").format(path=plugin_path))
        sys.exit(1)

    # Déterminer le répertoire de sortie
    # Nouvelle structure: <plugin>/__i18n_tmp__/Extractor/<timestamp>/
    if output_dir:
        # Override manuel (rétrocompatibilité)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamped_output_dir = os.path.join(output_dir, timestamp)
        os.makedirs(timestamped_output_dir, exist_ok=True)
    else:
        # Nouvelle structure dans le plugin
        timestamped_output_dir = get_tool_output_path(plugin_path, "Extractor", create=True)

    if not silent:
        print(f"\n" + _("EXTRACTION") + f" - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(_("Analyse de {plugin}...").format(plugin=os.path.basename(plugin_path)) + "\n")

    # Créer l'extracteur
    extractor = LocalizableStringExtractor(
        plugin_path=plugin_path,
        prefix=prefix,
        min_length=min_length,
        exclude_files=exclude_files,
        ignore_log=ignore_log
    )

    # Extraire
    extractor.extract_all()

    # Chemins des fichiers de sortie dans le sous-dossier timestampé
    strings_file = os.path.join(timestamped_output_dir, f"TranslatedStrings_{lang}.txt")
    spacing_file = os.path.join(timestamped_output_dir, "spacing_metadata.json")
    replacements_file = os.path.join(timestamped_output_dir, "replacements.json")
    report_file = os.path.join(timestamped_output_dir, f"extraction_report.txt")

    # Générateurs
    output_gen = OutputGenerator(plugin_path, prefix, silent=silent)
    report_gen = ReportGenerator(plugin_path, prefix, extractor.stats, silent=silent)

    # Générer les fichiers
    output_gen.generate_plugin_strings(extractor.extracted, strings_file, lang)
    output_gen.generate_spacing_metadata(extractor.spacing_metadata, extractor.text_to_key, spacing_file)
    output_gen.generate_replacements_json(extractor.extracted, replacements_file, extractor.text_to_key)
    report_gen.generate_report(extractor.extracted, extractor.spacing_metadata, report_file)

    # Préparer le résumé avec le formatteur
    formatter = OutputFormatter()

    # Compter les clés LOC existantes
    existing_loc_count = sum(1 for e in extractor.extracted if e.pattern_name == "existing_loc")

    # Statistiques principales
    main_stats = {
        _("Fichiers analysés"): extractor.stats.files_processed,
        _("Fichiers avec chaînes"): extractor.stats.files_with_strings,
        _("Total chaînes trouvées"): extractor.stats.total_strings,
        _("Clés uniques"): extractor.stats.unique_strings,
    }

    # Détails supplémentaires
    detail_stats = {
        _("Chaînes avec espaces"): extractor.stats.strings_with_spacing,
        _("Chaînes avec suffixes"): extractor.stats.strings_with_suffix,
        _("Lignes concaténées"): extractor.stats.concatenated_lines,
        _("Membres de concaténation"): extractor.stats.concat_members_total,
    }

    # Afficher le résumé formaté (sauf si silent)
    if not silent:
        formatter.print_extraction_summary(
            plugin_path=plugin_path,
            output_dir=timestamped_output_dir,
            prefix=prefix,
            lang=lang,
            main_stats=main_stats,
            detail_stats=detail_stats,
            existing_loc_count=existing_loc_count
        )

    # Afficher les fichiers générés (sauf si silent)
    if not silent:
        files_generated = [
            (f"TranslatedStrings_{lang}.txt", _("{n} clés").format(n=extractor.stats.unique_strings), _("Fichier de chaînes")),
            ("spacing_metadata.json", _("{n} entrées").format(n=len(extractor.spacing_metadata)), _("Métadonnées d'espaces/suffixes")),
            ("replacements.json", _("pour Applicator"), _("Remplacement des chaînes")),
            ("extraction_report.txt", _("rapport détaillé"), _("Analyse complète")),
        ]

        formatter.print_files_generated(files_generated, timestamped_output_dir, plugin_path)


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
            print("\n" + _("Extraction annulée"))
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
                            help='Override répertoire de sortie (défaut: <plugin>/__i18n_tmp__/Extractor/)')
        parser.add_argument('--prefix', default='$$$/Piwigo',
                            help='Préfixe des clés LOC (défaut: $$$/Piwigo)')
        # Charger la langue par défaut depuis config.json
        try:
            from tools.translator.config_loader import get_reference_lang
            default_lang = get_reference_lang()
        except:
            default_lang = 'en'

        parser.add_argument('--lang', default=default_lang,
                            help=f'Code langue (défaut: {default_lang})')
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
    # Si lancé directement (python main.py), re-lancer avec -m pour
    # préserver le contexte de package nécessaire aux imports relatifs
    if __package__ is None or __package__ == "":
        import subprocess
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.exit(subprocess.run(
            [sys.executable, "-m", "tools.extractor.main"] + sys.argv[1:],
            cwd=project_root
        ).returncode)
    main()
