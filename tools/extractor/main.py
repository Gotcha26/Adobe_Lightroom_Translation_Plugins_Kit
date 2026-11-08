#!/usr/bin/env python3
"""
Nom du fichier : main.py

Dépendances : .engine, .output, .report, .menu

Description :
Point d'entrée principal pour l'extraction des chaînes localisables d'un plugin Adobe Lightroom Classic.
Gère le mode CLI et le mode menu interactif. Lance l'extracteur, génère les fichiers de sortie et les rapports.

Usage CLI :
    python -m tools.extractor.main --plugin-path /path/to/plugin.lrplugin [options]

    python -m tools.extractor.main [--default-plugin PATH]   # Menu interactif

    Options:
        --plugin-path PATH    Chemin du plugin (active le mode CLI ; sans lui : menu)
        --default-plugin PATH Plugin pré-configuré pour le menu interactif
        --yes                 Aucune question (l'Extractor n'en pose pas en CLI)
        --output-dir PATH     Override du répertoire de sortie
        --prefix PREFIX       Préfixe LOC (défaut: config.json, sinon $$$/Plugin)
        --lang LANG           Code langue (défaut: en)
        --exclude FILE        Fichiers à exclure (répétable)
        --min-length N        Longueur minimale (défaut: 3)
        --no-ignore-log       NE PAS ignorer les logs

Date : 2026-11-08
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
from core.defaults import DEFAULT_PREFIX

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

    # Vérifier le chemin du plugin (l'appelant décide de la sortie : CLI, AUTO-SYNC…)
    if not os.path.isdir(plugin_path):
        raise FileNotFoundError(_("Répertoire introuvable: {path}").format(path=plugin_path))

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
        print("\n" + _("EXTRACTION") + f" - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
    strings_file = os.path.join(timestamped_output_dir, "TranslatedStrings_{lang}.txt".format(lang=lang))
    spacing_file = os.path.join(timestamped_output_dir, "spacing_metadata.json")
    replacements_file = os.path.join(timestamped_output_dir, "replacements.json")
    report_file = os.path.join(timestamped_output_dir, "extraction_report.txt")

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
            ("TranslatedStrings_{lang}.txt".format(lang=lang), _("{n} clés").format(n=extractor.stats.unique_strings), _("Fichier de chaînes")),
            ("spacing_metadata.json", _("{n} entrées").format(n=len(extractor.spacing_metadata)), _("Métadonnées d'espaces/suffixes")),
            ("replacements.json", _("pour Applicator"), _("Remplacement des chaînes")),
            ("extraction_report.txt", _("rapport détaillé"), _("Analyse complète")),
        ]

        formatter.print_files_generated(files_generated, timestamped_output_dir, plugin_path)


def _build_parser() -> argparse.ArgumentParser:
    """Parseur unique : mode interactif (sans --plugin-path) et mode CLI."""
    parser = argparse.ArgumentParser(
        description=_("Extrait les chaînes localisables d'un plugin Lightroom Classic"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_("""
Exemples:
  # Mode interactif (menu)
  python -m tools.extractor.main
  python -m tools.extractor.main --default-plugin ./piwigoPublish.lrplugin

  # Mode CLI
  python -m tools.extractor.main --plugin-path ./piwigoPublish.lrplugin
  python -m tools.extractor.main --plugin-path ./plugin --output-dir ./output
        """)
    )

    parser.add_argument('--default-plugin', default="",
                        help=_("Plugin pré-configuré pour le menu interactif"))
    parser.add_argument('--plugin-path', default=None,
                        help=_("Chemin vers le répertoire du plugin (active le mode CLI)"))
    parser.add_argument('--yes', action='store_true',
                        help=_("Aucune question (l'Extractor n'en pose pas en mode CLI)"))
    parser.add_argument('--output-dir', default=None,
                        help=_("Override répertoire de sortie (défaut: <plugin>/__i18n_tmp__/Extractor/)"))
    # Charger le préfixe et la langue par défaut depuis la configuration
    try:
        from tools.translator.config_loader import get_prefix
        default_prefix = get_prefix()
    except Exception as e:
        print(_("Préfixe illisible, {prefix} utilisé : {error}").format(prefix=DEFAULT_PREFIX, error=e))
        default_prefix = DEFAULT_PREFIX
    parser.add_argument('--prefix', default=default_prefix,
                        help=_("Préfixe des clés LOC (défaut: {prefix})").format(prefix=default_prefix))
    try:
        from tools.translator.config_loader import get_reference_lang
        default_lang = get_reference_lang()
    except Exception as e:
        print(_("Langue de référence illisible, « en » utilisée : {error}").format(error=e))
        default_lang = 'en'

    parser.add_argument('--lang', default=default_lang,
                        help=_("Code langue (défaut: {lang})").format(lang=default_lang))
    parser.add_argument('--exclude', action='append', default=[],
                        help=_("Fichiers à exclure (répétable)"))
    parser.add_argument('--min-length', type=int, default=3,
                        help=_("Longueur minimale des chaînes (défaut: 3)"))
    parser.add_argument('--no-ignore-log', action='store_true',
                        help=_("NE PAS ignorer les lignes de log"))
    return parser


def main():
    """Point d'entree principal.

    Mode interactif si --plugin-path est absent (--default-plugin pré-configure
    alors le plugin du menu) ; sinon mode CLI.
    """
    args = _build_parser().parse_args()

    if not args.plugin_path:
        # Menu interactif avec plugin pre-configure
        result = show_interactive_menu(args.default_plugin)

        if result is None:
            print("\n" + _("Extraction annulée"))
            sys.exit(1)

        plugin_path, output_dir, prefix, lang, exclude_files, min_length, ignore_log = result

        try:
            run_extraction(
                plugin_path=plugin_path,
                output_dir=output_dir,
                prefix=prefix,
                lang=lang,
                exclude_files=exclude_files,
                min_length=min_length,
                ignore_log=ignore_log
            )
        except FileNotFoundError as e:
            print(_("ERREUR: {error}").format(error=e))
            sys.exit(1)
    else:
        # Arguments en ligne de commande (l'Extractor ne pose aucune question en CLI)
        try:
            run_extraction(
                plugin_path=args.plugin_path,
                output_dir=args.output_dir or "",
                prefix=args.prefix,
                lang=args.lang,
                exclude_files=args.exclude,
                min_length=args.min_length,
                ignore_log=not args.no_ignore_log
            )
        except FileNotFoundError as e:
            print(_("ERREUR: {error}").format(error=e))
            sys.exit(1)


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
