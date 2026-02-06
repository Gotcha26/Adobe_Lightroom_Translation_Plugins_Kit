#!/usr/bin/env python3
"""
Nom du fichier : Translator_main.py

Dépendances : common, compare, compare_langs, extract, inject, sync, install, autosync, addlang, common.paths, common.colors

Description :
Gestionnaire de traductions multilingues pour plugins Adobe Lightroom Classic.

Orchestre le workflow complet de gestion des traductions :
  1. COMPARE: Compare 2 versions EN et génère UPDATE_en.json + CHANGELOG.txt
  2. EXTRACT: Génère fichiers TRANSLATE_xx.txt pour traduction
  3. INJECT: Réinjecte les traductions (valeur EN par défaut si non traduit)
  4. SYNC: Met à jour les langues avec EN
  5. INSTALL: Installe les fichiers dans le plugin
  6. AUTOSYNC: Synchronisation automatique
  7. ADDLANG: Ajoute une nouvelle langue

Modes :
  - Interactif: Menu complet avec workflow guidé
  - CLI: Commandes directes avec paramètres
  - Avancé: Options step-by-step pour la maintenance

Usage CLI :
    python Translator_main.py                           # Mode interactif
    python Translator_main.py compare --old old.txt --new new.txt --plugin-path ./plugin.lrplugin
    python Translator_main.py extract --plugin-path ./plugin.lrplugin --locales ./Locales
    python Translator_main.py inject --plugin-path ./plugin.lrplugin --locales ./Locales
    python Translator_main.py sync --plugin-path ./plugin.lrplugin --locales ./Locales
    python Translator_main.py compare-langs --lang1 fr --lang2 de --locales ./Locales

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import argparse

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.paths import get_tool_output_path, find_latest_tool_output
from core.colors import Colors
from core.i18n import _

from .common import clear_screen, print_header
from .compare import run_compare, menu_compare
from .compare_langs import run_compare_langs, menu_compare_langs
from .extract import run_extract, run_extract_all, menu_extract
from .inject import run_inject, run_inject_from_dir, menu_inject
from .sync import run_sync, generate_sync_report, menu_sync
from .install import menu_install, run_install
from .autosync import menu_autosync, run_autosync
from .addlang import menu_addlang, run_addlang_cli

# Instance couleurs
c = Colors()


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def advanced_menu(plugin_path: str):
    """Menu des options avancées (workflow manuel)."""
    while True:
        clear_screen()
        print_header()

        print(_("\n{var0}  OPTIONS AVANCÉES{var1}").format(var0=c.TITLE, var1=c.RESET))
        print(_("  {var0}Workflow manuel étape par étape{var1}").format(var0=c.DIM, var1=c.RESET))
        print(c.separator())

        # Afficher le plugin configuré
        if plugin_path:
            print(_("\n{var0}[INFO]{var1} Plugin: {var2}{var3}{var4}").format(var0=c.INFO, var1=c.RESET, var2=c.VALUE, var3=os.path.basename(plugin_path), var4=c.RESET))
        else:
            print(_("\n{var0}[ATTENTION]{var1} Aucun plugin configuré - utilise répertoires locaux").format(var0=c.WARNING, var1=c.RESET))

        print(_("\n{var0}  Commandes:{var1}").format(var0=c.TITLE, var1=c.RESET))
        print(c.separator())
        print(_("  {var0}1{var1}. {var2}COMPARE{var3}       - Comparer 2 versions EN").format(var0=c.YELLOW, var1=c.RESET, var2=c.INFO, var3=c.RESET))
        print(_("  {var0}2{var1}. {var2}COMPARE-LANGS{var3} - Comparer 2 fichiers de langues").format(var0=c.YELLOW, var1=c.RESET, var2=c.INFO, var3=c.RESET))
        print(_("  {var0}3{var1}. {var2}EXTRACT{var3}       - Extraire les clés à traduire").format(var0=c.YELLOW, var1=c.RESET, var2=c.INFO, var3=c.RESET))
        print(_("  {var0}4{var1}. {var2}INJECT{var3}        - Réinjecter les traductions").format(var0=c.YELLOW, var1=c.RESET, var2=c.INFO, var3=c.RESET))
        print(_("  {var0}5{var1}. {var2}SYNC{var3}          - Synchroniser les langues avec EN").format(var0=c.YELLOW, var1=c.RESET, var2=c.INFO, var3=c.RESET))
        print()
        print(c.separator())
        print(_("  {var0}8{var1}. {var2}Aide{var3}          - Documentation complète").format(var0=c.YELLOW, var1=c.RESET, var2=c.CYAN, var3=c.RESET))
        print(_("  {var0}0{var1}. {var2}Retour au menu principal{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.DIM, var3=c.RESET))
        print(c.separator())

        choice = input(c.prompt(_("Votre choix:") + " (0-8): ")).strip()

        if choice == '1':
            menu_compare(plugin_path)
        elif choice == '2':
            menu_compare_langs(plugin_path)
        elif choice == '3':
            menu_extract(plugin_path)
        elif choice == '4':
            menu_inject(plugin_path)
        elif choice == '5':
            menu_sync(plugin_path)
        elif choice == '8':
            clear_screen()
            print(__doc__)
            input(_("\n{var0}Appuyez sur Entrée pour revenir au menu...{var1}").format(var0=c.DIM, var1=c.RESET))
        elif choice == '0':
            return  # Retour au menu principal
        else:
            print(c.error(_("Choix invalide : \"){choice}\""))
            input(_("{var0}Appuyez sur Entrée...{var1}").format(var0=c.DIM, var1=c.RESET))


def main_menu(default_plugin_path: str = ""):
    """Menu principal interactif.

    Args:
        default_plugin_path: Chemin du plugin pré-configuré (optionnel)
    """
    # Demander le chemin du plugin si non fourni
    plugin_path = default_plugin_path

    if not plugin_path:
        clear_screen()
        print_header()
        print(_("\n{var0}Configuration initiale{var1}").format(var0=c.INFO, var1=c.RESET))
        print(c.separator())
        print(_("\n{var0}Chemin du plugin{var1} (.lrplugin) {var2}(x pour annuler){var3}:").format(var0=c.KEY, var1=c.RESET, var2=c.DIM, var3=c.RESET))
        print(f"{c.DIM}  (Optionnel - permet d'utiliser la structure __i18n_tmp__){c.RESET}")
        print(_("{var0}  (Entrée pour ignorer - utilise répertoires locaux){var1}").format(var0=c.DIM, var1=c.RESET))
        plugin_path = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if plugin_path.lower() == 'x':
            print(_("\n{var0}Annulation{var1}").format(var0=c.DIM, var1=c.RESET))
            sys.exit(0)

    # Valider le chemin du plugin si fourni
    if plugin_path:
        from core.paths import validate_plugin_path
        is_valid, normalized, error = validate_plugin_path(plugin_path)
        if is_valid:
            plugin_path = normalized
        else:
            print(c.warning(_("Chemin invalide: {error}").format(error=error)))
            print(_("{var0}Vous pouvez continuer sans plugin (répertoires locaux){var1}").format(var0=c.DIM, var1=c.RESET))
            plugin_path = ""
            input(_("{var0}Appuyez sur Entrée pour continuer...{var1}").format(var0=c.DIM, var1=c.RESET))

    while True:
        clear_screen()
        print_header()

        # Afficher le plugin configuré
        if plugin_path:
            print(_("\n{var0}[INFO]{var1} Plugin: {var2}{var3}{var4}").format(var0=c.INFO, var1=c.RESET, var2=c.VALUE, var3=os.path.basename(plugin_path), var4=c.RESET))
        else:
            print(_("\n{var0}[ATTENTION]{var1} Aucun plugin configuré - utilise répertoires locaux").format(var0=c.WARNING, var1=c.RESET))

        print(_("\n{var0}  Options essentielles:{var1}").format(var0=c.TITLE, var1=c.RESET))
        print(c.separator())
        print(_("  {var0}1{var1}. {var2}INSTALL{var3}          - Première installation").format(var0=c.YELLOW, var1=c.RESET, var2=c.SUCCESS, var3=c.RESET))
        print(_("  {var0}2{var1}. {var2}AUTO-SYNC{var3} ⭐     - Maintenance automatique").format(var0=c.YELLOW, var1=c.RESET, var2=c.SUCCESS, var3=c.RESET))
        print(_("  {var0}3{var1}. {var2}ADD LANGUAGE{var3}     - Ajouter/réinstaller une langue").format(var0=c.YELLOW, var1=c.RESET, var2=c.SUCCESS, var3=c.RESET))
        print()
        print(c.separator())
        print(_("  {var0}7{var1}. {var2}Options avancées{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.CYAN, var3=c.RESET))
        print(_("  {var0}9{var1}. {var2}Changer le plugin{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.CYAN, var3=c.RESET))
        print(_("  {var0}0{var1}. {var2}Quitter{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.DIM, var3=c.RESET))
        print(c.separator())

        choice = input(c.prompt(_("Votre choix:") + " (0-9): ")).strip()

        if choice == '1':
            menu_install(plugin_path)
        elif choice == '2':
            menu_autosync(plugin_path)
        elif choice == '3':
            menu_addlang(plugin_path)
        elif choice == '7':
            advanced_menu(plugin_path)
        elif choice == '9':
            # Changer le plugin
            clear_screen()
            print_header()
            print(_("\n{var0}Changement de plugin{var1}").format(var0=c.INFO, var1=c.RESET))
            print(c.separator())
            print(_("\n{var0}Nouveau chemin du plugin{var1} (.lrplugin) {var2}(x pour annuler){var3}:").format(var0=c.KEY, var1=c.RESET, var2=c.DIM, var3=c.RESET))
            print(_("{var0}  (Entrée pour ignorer - utilise répertoires locaux){var1}").format(var0=c.DIM, var1=c.RESET))
            new_path = input(f"{c.PROMPT}  > {c.RESET}").strip()

            if new_path.lower() == 'x':
                continue  # Annulation immédiate, retour au menu

            if new_path:
                from core.paths import validate_plugin_path
                is_valid, normalized, error = validate_plugin_path(new_path)
                if is_valid:
                    plugin_path = normalized
                    print(c.success(_("Plugin changé: {var0}{plugin_path}{var2}").format(var0=c.VALUE, plugin_path=plugin_path, var2=c.RESET)))
                else:
                    print(c.error(_("Chemin invalide: {error}").format(error=error)))
            else:
                plugin_path = ""
                print(c.success(_("Plugin désactivé - utilise répertoires locaux")))

            input(_("\n{var0}Appuyez sur Entrée pour continuer...{var1}").format(var0=c.DIM, var1=c.RESET))
        elif choice == '0':
            print(_("\n{var0}Au revoir !{var1}").format(var0=c.DIM, var1=c.RESET))
            break  # Sortir du menu principal
        else:
            print(c.error(_("Choix invalide : \"){choice}\""))
            input(_("{var0}Appuyez sur Entrée...{var1}").format(var0=c.DIM, var1=c.RESET))


# =============================================================================
# CLI
# =============================================================================

def main():
    """Point d'entrée principal."""

    # Vérifier si mode interactif (aucun argument ou seulement --default-plugin)
    if len(sys.argv) == 1 or (len(sys.argv) == 3 and sys.argv[1] == '--default-plugin'):
        # Récupérer le chemin par défaut si fourni
        default_plugin = ""
        if len(sys.argv) == 3 and sys.argv[1] == '--default-plugin':
            default_plugin = sys.argv[2]

        main_menu(default_plugin)
        return

    # Mode AUTO-SYNC direct (lancé depuis LocalizationToolKit)
    if len(sys.argv) == 4 and sys.argv[1] == '--plugin-path' and sys.argv[3] == '--autosync':
        plugin_path = sys.argv[2]
        if not os.path.isdir(plugin_path):
            print(c.error(_("Plugin introuvable: {plugin_path}").format(plugin_path=plugin_path)))
            sys.exit(1)
        results = run_autosync(plugin_path)
        from .autosync import print_autosync_report
        print_autosync_report(results, plugin_path)
        return

    parser = argparse.ArgumentParser(
        description=_("Gestionnaire de traductions multilingues"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Mode interactif
  python Translator_main.py

  # Avec --plugin-path (structure __i18n_tmp__):
  python Translator_main.py compare --old ./old/en.txt --new ./new/en.txt --plugin-path ./plugin.lrplugin
  python Translator_main.py compare-langs --lang1 fr --lang2 de --locales ./plugin.lrplugin --plugin-path ./plugin.lrplugin
  python Translator_main.py extract --plugin-path ./plugin.lrplugin --locales ./plugin.lrplugin
  python Translator_main.py sync --plugin-path ./plugin.lrplugin --locales ./plugin.lrplugin

  # Mode legacy (sans plugin-path):
  python Translator_main.py compare --old ./v1/en.txt --new ./v2/en.txt
  python Translator_main.py compare-langs --file1 ./Locales/fr.txt --file2 ./Locales/de.txt
  python Translator_main.py extract --update ./20260128_143000 --locales ./Locales
  python Translator_main.py sync --update ./20260128_143000 --locales ./Locales
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commande')

    # compare
    compare_parser = subparsers.add_parser('compare', help='Compare deux versions EN')
    compare_parser.add_argument('--old', required=True, help='Ancien fichier EN')
    compare_parser.add_argument('--new', required=True, help='Nouveau fichier EN')
    compare_parser.add_argument('--plugin-path', help='Chemin plugin (sortie: __i18n_tmp__/3_Translator/)')
    compare_parser.add_argument('--output', help='Override repertoire de sortie')

    # compare-langs
    compare_langs_parser = subparsers.add_parser('compare-langs', help='Compare deux fichiers de langues')
    compare_langs_parser.add_argument('--file1', help='Premier fichier (ou repertoire)')
    compare_langs_parser.add_argument('--file2', help='Second fichier (ou repertoire)')
    compare_langs_parser.add_argument('--lang1', help='Code langue 1 (ex: fr) - cherche dans --locales')
    compare_langs_parser.add_argument('--lang2', help='Code langue 2 (ex: de) - cherche dans --locales')
    compare_langs_parser.add_argument('--locales', help='Repertoire des traductions (requis avec --lang1/--lang2)')
    compare_langs_parser.add_argument('--plugin-path', help='Chemin plugin (sortie: __i18n_tmp__/3_Translator/)')
    compare_langs_parser.add_argument('--output', help='Override repertoire de sortie')

    # extract
    extract_parser = subparsers.add_parser('extract', help='Genere fichiers TRANSLATE_*.txt')
    extract_parser.add_argument('--update', help='Dossier UPDATE (ou auto-detection si --plugin-path)')
    extract_parser.add_argument('--plugin-path', help='Chemin plugin (auto-detection __i18n_tmp__/)')
    extract_parser.add_argument('--locales', help='Repertoire des traductions existantes')
    extract_parser.add_argument('--lang', help='Langue specifique (defaut: toutes)')
    extract_parser.add_argument('--output', help='Override repertoire de sortie')

    # inject
    inject_parser = subparsers.add_parser('inject', help='Injecte les traductions')
    inject_parser.add_argument('--translate', help='Fichier TRANSLATE_xx.txt')
    inject_parser.add_argument('--target', help='Fichier TranslatedStrings_xx.txt cible')
    inject_parser.add_argument('--translate-dir', help='Dossier contenant TRANSLATE_*.txt')
    inject_parser.add_argument('--plugin-path', help='Chemin plugin (auto-detection __i18n_tmp__/)')
    inject_parser.add_argument('--locales', help='Dossier des fichiers de langue')
    inject_parser.add_argument('--update', help='Dossier UPDATE (pour valeurs EN)')

    # sync
    sync_parser = subparsers.add_parser('sync', help='Synchronise les langues')
    sync_parser.add_argument('--ref', help='Fichier EN de reference')
    sync_parser.add_argument('--plugin-path', help='Chemin plugin (auto-detection __i18n_tmp__/)')
    sync_parser.add_argument('--locales', help='Repertoire des fichiers de langues')
    sync_parser.add_argument('--update', help='Dossier UPDATE (avec UPDATE_en.json)')

    args = parser.parse_args()

    if args.command == 'compare':
        try:
            print(_("{var0}[INFO]{var1} Comparaison...").format(var0=c.INFO, var1=c.RESET))
            # Determiner le repertoire de sortie
            if args.output:
                output_dir = args.output
            elif hasattr(args, 'plugin_path') and args.plugin_path:
                output_dir = get_tool_output_path(args.plugin_path, "Translator", create=True)
            else:
                output_dir = None  # run_compare creera un dossier timestampe local
            output_dir = run_compare(args.old, args.new, output_dir)

            import json
            with open(os.path.join(output_dir, 'UPDATE_en.json'), 'r', encoding='utf-8') as f:
                result = json.load(f)

            summary = result['summary']
            print(f"\n{c.HEADER}{'=' * 60}{c.RESET}")
            print(_("{var0}RÉSUMÉ{var1}").format(var0=c.TITLE, var1=c.RESET))
            print(f"{c.HEADER}{'=' * 60}{c.RESET}")
            print(_("{var0}Clés ajoutées   {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.GREEN, var3=summary['added'], var4=c.RESET))
            print(_("{var0}Clés modifiées  {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.YELLOW, var3=summary['changed'], var4=c.RESET))
            print(_("{var0}Clés supprimées {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.RED, var3=summary['deleted'], var4=c.RESET))
            print(_("{var0}Clés inchangées {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.DIM, var3=summary['unchanged'], var4=c.RESET))
            print(c.success(_("Fichiers générés dans: {var0}{output_dir}{var2}").format(var0=c.VALUE, output_dir=output_dir, var2=c.RESET)))

        except Exception as e:
            print(c.error(_("Erreur: {e}").format(e=e)))
            sys.exit(1)

    elif args.command == 'compare-langs':
        try:
            import json
            print(_("{var0}[INFO]{var1} Comparaison de langues...").format(var0=c.INFO, var1=c.RESET))

            # Déterminer les fichiers à comparer
            file1 = None
            file2 = None
            lang1_name = None
            lang2_name = None

            # Mode 1: Par codes langue (--lang1 --lang2 --locales)
            if args.lang1 and args.lang2:
                if not args.locales:
                    print(c.error(_("--locales requis avec --lang1 et --lang2")))
                    sys.exit(1)

                file1 = os.path.join(args.locales, f'TranslatedStrings_{args.lang1}.txt')
                file2 = os.path.join(args.locales, f'TranslatedStrings_{args.lang2}.txt')
                lang1_name = args.lang1
                lang2_name = args.lang2

                if not os.path.isfile(file1):
                    print(c.error(_("Fichier non trouvé: {file1}").format(file1=file1)))
                    sys.exit(1)
                if not os.path.isfile(file2):
                    print(c.error(_("Fichier non trouvé: {file2}").format(file2=file2)))
                    sys.exit(1)

            # Mode 2: Par chemins de fichiers (--file1 --file2)
            elif args.file1 and args.file2:
                file1 = args.file1
                file2 = args.file2
                # lang1_name et lang2_name seront auto-détectés

            else:
                print(c.error(_("Spécifiez soit --lang1 + --lang2 + --locales, soit --file1 + --file2")))
                sys.exit(1)

            # Déterminer le répertoire de sortie
            if args.output:
                output_dir = args.output
            elif hasattr(args, 'plugin_path') and args.plugin_path:
                output_dir = get_tool_output_path(args.plugin_path, "Translator", create=True)
            else:
                output_dir = None  # run_compare_langs créera un dossier timestampé local

            # Exécuter la comparaison
            output_dir = run_compare_langs(file1, file2, lang1_name, lang2_name, output_dir)

            # Charger et afficher le résultat
            with open(os.path.join(output_dir, 'COMPARE_LANGS_data.json'), 'r', encoding='utf-8') as f:
                result = json.load(f)

            stats = result['statistics']
            l1 = result['lang1_name']
            l2 = result['lang2_name']

            print(f"\n{c.HEADER}{'=' * 60}{c.RESET}")
            print(_("{var0}RÉSUMÉ - COMPARAISON DE LANGUES{var1}").format(var0=c.TITLE, var1=c.RESET))
            print(f"{c.HEADER}{'=' * 60}{c.RESET}")
            print(_("{var0}Langue 1{var1}: {var2}{l1}{var4} ({var5} clés)").format(var0=c.KEY, var1=c.RESET, var2=c.CYAN, l1=l1, var4=c.RESET, var5=stats['keys_in_lang1']))
            print(_("{var0}Langue 2{var1}: {var2}{l2}{var4} ({var5} clés)").format(var0=c.KEY, var1=c.RESET, var2=c.CYAN, l2=l2, var4=c.RESET, var5=stats['keys_in_lang2']))
            print()
            print(_("{var0}Clés totales uniques    {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.VALUE, var3=stats['total_unique_keys'], var4=c.RESET))
            print(_("{var0}Clés dans les deux      {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.GREEN, var3=stats['keys_in_both'], var4=c.RESET))
            print(_("{var0}Seulement dans {l1:<7s}{var2}: {var3}{var4}{var5}").format(var0=c.KEY, l1=l1, var2=c.RESET, var3=c.YELLOW, var4=stats['only_lang1'], var5=c.RESET))
            print(_("{var0}Seulement dans {l2:<7s}{var2}: {var3}{var4}{var5}").format(var0=c.KEY, l2=l2, var2=c.RESET, var3=c.YELLOW, var4=stats['only_lang2'], var5=c.RESET))
            print()
            print(_("{var0}Valeurs identiques      {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.DIM, var3=stats['identical_values_count'], var4=c.RESET))
            print(_("{var0}Valeurs différentes     {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.VALUE, var3=stats['different_values_count'], var4=c.RESET))

            if stats['identical_values_count'] > 0 and (l1 == 'EN' or l2 == 'EN'):
                print(_("\n{var0}⚠️  {var1} traduction(s) identique(s) à EN détectée(s)!{var2}").format(var0=c.WARNING, var1=stats['identical_values_count'], var2=c.RESET))

            print(c.success(_("\nFichiers générés dans: {var0}{output_dir}{var2}").format(var0=c.VALUE, output_dir=output_dir, var2=c.RESET)))

        except Exception as e:
            print(c.error(_("Erreur: {e}").format(e=e)))
            import traceback
            traceback.print_exc()
            sys.exit(1)

    elif args.command == 'extract':
        try:
            print(_("{var0}[INFO]{var1} Extraction...").format(var0=c.INFO, var1=c.RESET))
            # Determiner le dossier UPDATE
            update_dir = args.update
            if not update_dir and hasattr(args, 'plugin_path') and args.plugin_path:
                update_dir = find_latest_tool_output(args.plugin_path, "Translator")
                if not update_dir:
                    print(c.error(_("Aucun dossier Translator trouvé dans __i18n_tmp__/")))
                    print(f"{c.DIM}        Lancez d'abord la commande 'compare'.{c.RESET}")
                    sys.exit(1)
                print(_("{var0}[INFO]{var1} Auto-détection: {var2}{update_dir}{var4}").format(var0=c.INFO, var1=c.RESET, var2=c.VALUE, update_dir=update_dir, var4=c.RESET))

            if not update_dir:
                print(c.error(_("--update ou --plugin-path requis")))
                sys.exit(1)

            output_dir = args.output
            if args.lang:
                output_file = run_extract(update_dir, args.lang, args.locales, output_dir)
                print(c.success(_("Généré: {var0}{output_file}{var2}").format(var0=c.VALUE, output_file=output_file, var2=c.RESET)))
            else:
                generated = run_extract_all(update_dir, args.locales, output_dir)
                print(_("\n{var0}[OK]{var1} {var2}{var3}{var4} fichier(s) généré(s):").format(var0=c.OK, var1=c.RESET, var2=c.WHITE, var3=len(generated), var4=c.RESET))
                for f in generated:
                    print(f"  {c.DIM}-{c.RESET} {c.VALUE}{os.path.basename(f)}{c.RESET}")

        except Exception as e:
            print(c.error(_("Erreur: {e}").format(e=e)))
            sys.exit(1)

    elif args.command == 'inject':
        try:
            # Auto-detection du dossier translate si plugin_path fourni
            translate_dir = args.translate_dir
            update_dir = args.update
            if hasattr(args, 'plugin_path') and args.plugin_path and not translate_dir:
                translate_dir = find_latest_tool_output(args.plugin_path, "Translator")
                update_dir = update_dir or translate_dir
                if translate_dir:
                    print(_("{var0}[INFO]{var1} Auto-détection: {var2}{translate_dir}{var4}").format(var0=c.INFO, var1=c.RESET, var2=c.VALUE, translate_dir=translate_dir, var4=c.RESET))

            if args.translate and args.target:
                print(_("{var0}[INFO]{var1} Injection...").format(var0=c.INFO, var1=c.RESET))
                stats = run_inject(args.translate, args.target, update_dir)
                print(c.success(_("{var0}{var1}{var2} traduites + {var3}{var4}{var5} EN par défaut").format(var0=c.GREEN, var1=stats['injected'], var2=c.RESET, var3=c.CYAN, var4=stats['from_en'], var5=c.RESET)))
            elif translate_dir and args.locales:
                print(_("{var0}[INFO]{var1} Injection...").format(var0=c.INFO, var1=c.RESET))
                results = run_inject_from_dir(translate_dir, args.locales, update_dir)
                for lang, stats in sorted(results.items()):
                    if 'error' in stats:
                        print(_("{var0}[{var1}]{var2} {var3}[ERREUR]{var4}: {var5}").format(var0=c.CYAN, var1=lang.upper(), var2=c.RESET, var3=c.ERROR, var4=c.RESET, var5=stats['error']))
                    else:
                        print(_("{var0}[{var1}]{var2} {var3}[OK]{var4}: {var5}{var6}{var7} traduites + {var8}{var9}{var10} EN").format(var0=c.CYAN, var1=lang.upper(), var2=c.RESET, var3=c.OK, var4=c.RESET, var5=c.GREEN, var6=stats['injected'], var7=c.RESET, var8=c.CYAN, var9=stats['from_en'], var10=c.RESET))
            else:
                print(c.error(_("Spécifiez --translate + --target OU --translate-dir + --locales OU --plugin-path + --locales")))
                sys.exit(1)

        except Exception as e:
            print(c.error(_("Erreur: {e}").format(e=e)))
            sys.exit(1)

    elif args.command == 'sync':
        try:
            # Auto-detection du dossier update si plugin_path fourni
            update_dir = args.update
            if hasattr(args, 'plugin_path') and args.plugin_path and not update_dir:
                update_dir = find_latest_tool_output(args.plugin_path, "Translator")
                if update_dir:
                    print(_("{var0}[INFO]{var1} Auto-détection: {var2}{update_dir}{var4}").format(var0=c.INFO, var1=c.RESET, var2=c.VALUE, update_dir=update_dir, var4=c.RESET))

            if not args.ref and not update_dir:
                print(c.error(_("--ref, --update ou --plugin-path requis")))
                sys.exit(1)

            print(_("{var0}[INFO]{var1} Synchronisation...").format(var0=c.INFO, var1=c.RESET))
            results = run_sync(args.ref, args.locales, update_dir)

            if not results:
                print(c.warning(_("Aucune langue étrangère trouvée.")))
            else:
                print()
                print(generate_sync_report(results))

        except Exception as e:
            print(c.error(_("Erreur: {e}").format(e=e)))
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    # Si lancé directement (python main.py), re-lancer avec -m pour
    # préserver le contexte de package nécessaire aux imports relatifs
    if __package__ is None or __package__ == "":
        import subprocess
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.exit(subprocess.run(
            [sys.executable, "-m", "tools.translator.main"] + sys.argv[1:],
            cwd=project_root
        ).returncode)
    main()
