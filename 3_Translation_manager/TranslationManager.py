#!/usr/bin/env python3
"""
TranslationManager.py

Gestionnaire de traductions multilingues pour plugins Adobe Lightroom Classic.

================================================================================
COMMANDES
================================================================================

  compare   Compare 2 versions EN → UPDATE_en.json + CHANGELOG.txt
  extract   Génère mini fichiers TRANSLATE_xx.txt pour traduction
  inject    Réinjecte les traductions (valeur EN par défaut si non traduit)
  sync      Met à jour les langues avec EN

================================================================================
WORKFLOW
================================================================================

  Code LUA modifié
        │
        ▼
  Extractor → TranslatedStrings_en.txt (nouveau)
        │
        ▼
  1. COMPARE: ancien EN vs nouveau EN
        │
        ▼
  2. EXTRACT: génère TRANSLATE_xx.txt (optionnel)
        │
        ▼
  3. INJECT: fusionne les traductions (optionnel)
        │
        ▼
  4. SYNC: finalise les fichiers

================================================================================
USAGE
================================================================================

Mode interactif:
    python TranslationManager.py

Mode CLI (avec --plugin-path pour structure __i18n_tmp__):
    python TranslationManager.py compare --old ancien.txt --new nouveau.txt --plugin-path ./plugin.lrplugin
    python TranslationManager.py extract --plugin-path ./plugin.lrplugin --locales ./Locales
    python TranslationManager.py inject --plugin-path ./plugin.lrplugin --locales ./Locales
    python TranslationManager.py sync --plugin-path ./plugin.lrplugin --locales ./Locales

Mode CLI (legacy):
    python TranslationManager.py compare --old ancien.txt --new nouveau.txt
    python TranslationManager.py extract --update ./20260128_143000 --locales ./Locales
    python TranslationManager.py inject --translate-dir ./20260128_143000 --locales ./Locales
    python TranslationManager.py sync --update ./20260128_143000 --locales ./Locales

Sorties generees dans: <plugin>/__i18n_tmp__/TranslationManager/<timestamp>/

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-01-30
Version: 6.0 - Ajout des couleurs + Structure __i18n_tmp__
"""

import os
import sys
import argparse

# Ajouter le répertoire courant et parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.paths import get_tool_output_path, find_latest_tool_output
from common.colors import Colors

from TM_common import clear_screen, print_header
from TM_compare import run_compare, menu_compare
from TM_extract import run_extract, run_extract_all, menu_extract
from TM_inject import run_inject, run_inject_from_dir, menu_inject
from TM_sync import run_sync, generate_sync_report, menu_sync

# Instance couleurs
c = Colors()


# =============================================================================
# MENU INTERACTIF
# =============================================================================

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
        print(f"\n{c.INFO}Configuration initiale{c.RESET}")
        print(c.separator())
        print(f"\n{c.KEY}Chemin du plugin{c.RESET} (.lrplugin):")
        print(f"{c.DIM}  (Optionnel - permet d'utiliser la structure __i18n_tmp__){c.RESET}")
        print(f"{c.DIM}  (Entrée pour ignorer - utilise répertoires locaux){c.RESET}")
        plugin_path = input(f"{c.PROMPT}  > {c.RESET}").strip()

    # Valider le chemin du plugin si fourni
    if plugin_path:
        from common.paths import validate_plugin_path
        is_valid, normalized, error = validate_plugin_path(plugin_path)
        if is_valid:
            plugin_path = normalized
            print(f"\n{c.OK}[OK]{c.RESET} Plugin validé: {c.VALUE}{plugin_path}{c.RESET}")
            input(f"{c.DIM}Appuyez sur Entrée pour continuer...{c.RESET}")
        else:
            print(c.warning(f"Chemin invalide: {error}"))
            print(f"{c.DIM}Vous pouvez continuer sans plugin (répertoires locaux){c.RESET}")
            plugin_path = ""
            input(f"{c.DIM}Appuyez sur Entrée pour continuer...{c.RESET}")

    while True:
        clear_screen()
        print_header()

        # Afficher le plugin configuré
        if plugin_path:
            print(f"\n{c.INFO}[INFO]{c.RESET} Plugin: {c.VALUE}{os.path.basename(plugin_path)}{c.RESET}")
        else:
            print(f"\n{c.WARNING}[ATTENTION]{c.RESET} Aucun plugin configuré - utilise répertoires locaux")

        print(f"\n{c.TITLE}  Options:{c.RESET}")
        print(c.separator())
        print(f"  {c.YELLOW}1{c.RESET}. {c.INFO}COMPARE{c.RESET}")
        print(f"     {c.DIM}Compare ancien EN vs nouveau EN{c.RESET}")
        print(f"     {c.DIM}→ Génère UPDATE_en.json + CHANGELOG.txt{c.RESET}")
        print()
        print(f"  {c.YELLOW}2{c.RESET}. {c.INFO}EXTRACT{c.RESET} {c.DIM}(optionnel){c.RESET}")
        print(f"     {c.DIM}Génère mini fichiers TRANSLATE_xx.txt pour traduction{c.RESET}")
        print()
        print(f"  {c.YELLOW}3{c.RESET}. {c.INFO}INJECT{c.RESET} {c.DIM}(optionnel){c.RESET}")
        print(f"     {c.DIM}Réinjecte les traductions (EN par défaut si vide){c.RESET}")
        print()
        print(f"  {c.YELLOW}4{c.RESET}. {c.INFO}SYNC{c.RESET}")
        print(f"     {c.DIM}Met à jour les langues avec EN{c.RESET}")
        print(f"     {c.DIM}→ Ajoute [NEW], marque [NEEDS_REVIEW], supprime obsolètes{c.RESET}")
        print()
        print(f"  {c.YELLOW}5{c.RESET}. {c.CYAN}Aide{c.RESET}")
        print()
        print(f"  {c.YELLOW}9{c.RESET}. {c.CYAN}Changer le plugin{c.RESET}")
        print()
        print(f"  {c.YELLOW}0{c.RESET}. {c.DIM}Quitter{c.RESET}")
        print(c.separator())

        choice = input(f"\n{c.PROMPT}  Votre choix (0-5, 9): {c.RESET}").strip()

        if choice == '1':
            menu_compare(plugin_path)
            input(f"\n{c.DIM}  Appuyez sur Entrée pour continuer...{c.RESET}")
        elif choice == '2':
            menu_extract(plugin_path)
            input(f"\n{c.DIM}  Appuyez sur Entrée pour continuer...{c.RESET}")
        elif choice == '3':
            menu_inject(plugin_path)
        elif choice == '4':
            menu_sync(plugin_path)
        elif choice == '5':
            clear_screen()
            print(__doc__)
            input(f"\n{c.DIM}Appuyez sur Entrée pour revenir au menu...{c.RESET}")
        elif choice == '9':
            # Changer le plugin
            clear_screen()
            print_header()
            print(f"\n{c.INFO}Changement de plugin{c.RESET}")
            print(c.separator())
            print(f"\n{c.KEY}Nouveau chemin du plugin{c.RESET} (.lrplugin):")
            print(f"{c.DIM}  (Entrée pour ignorer - utilise répertoires locaux){c.RESET}")
            new_path = input(f"{c.PROMPT}  > {c.RESET}").strip()

            if new_path:
                from common.paths import validate_plugin_path
                is_valid, normalized, error = validate_plugin_path(new_path)
                if is_valid:
                    plugin_path = normalized
                    print(c.success(f"Plugin changé: {c.VALUE}{plugin_path}{c.RESET}"))
                else:
                    print(c.error(f"Chemin invalide: {error}"))
            else:
                plugin_path = ""
                print(c.success("Plugin désactivé - utilise répertoires locaux"))

            input(f"\n{c.DIM}Appuyez sur Entrée pour continuer...{c.RESET}")
        elif choice == '0':
            print(f"\n{c.SUCCESS}  Au revoir!{c.RESET}")
            break
        else:
            print(c.error("Choix invalide."))
            input(f"{c.DIM}Appuyez sur Entrée...{c.RESET}")


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
    
    parser = argparse.ArgumentParser(
        description="Gestionnaire de traductions multilingues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Mode interactif
  python TranslationManager.py

  # Avec --plugin-path (structure __i18n_tmp__):
  python TranslationManager.py compare --old ./old/en.txt --new ./new/en.txt --plugin-path ./plugin.lrplugin
  python TranslationManager.py extract --plugin-path ./plugin.lrplugin --locales ./plugin.lrplugin
  python TranslationManager.py sync --plugin-path ./plugin.lrplugin --locales ./plugin.lrplugin

  # Mode legacy (sans plugin-path):
  python TranslationManager.py compare --old ./v1/en.txt --new ./v2/en.txt
  python TranslationManager.py extract --update ./20260128_143000 --locales ./Locales
  python TranslationManager.py sync --update ./20260128_143000 --locales ./Locales
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commande')
    
    # compare
    compare_parser = subparsers.add_parser('compare', help='Compare deux versions EN')
    compare_parser.add_argument('--old', required=True, help='Ancien fichier EN')
    compare_parser.add_argument('--new', required=True, help='Nouveau fichier EN')
    compare_parser.add_argument('--plugin-path', help='Chemin plugin (sortie: __i18n_tmp__/TranslationManager/)')
    compare_parser.add_argument('--output', help='Override repertoire de sortie')
    
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
            print(f"{c.INFO}[INFO]{c.RESET} Comparaison...")
            # Determiner le repertoire de sortie
            if args.output:
                output_dir = args.output
            elif hasattr(args, 'plugin_path') and args.plugin_path:
                output_dir = get_tool_output_path(args.plugin_path, "TranslationManager", create=True)
            else:
                output_dir = None  # run_compare creera un dossier timestampe local
            output_dir = run_compare(args.old, args.new, output_dir)

            import json
            with open(os.path.join(output_dir, 'UPDATE_en.json'), 'r', encoding='utf-8') as f:
                result = json.load(f)

            summary = result['summary']
            print(f"\n{c.HEADER}{'=' * 60}{c.RESET}")
            print(f"{c.TITLE}RÉSUMÉ{c.RESET}")
            print(f"{c.HEADER}{'=' * 60}{c.RESET}")
            print(f"{c.KEY}Clés ajoutées   {c.RESET}: {c.GREEN}{summary['added']}{c.RESET}")
            print(f"{c.KEY}Clés modifiées  {c.RESET}: {c.YELLOW}{summary['changed']}{c.RESET}")
            print(f"{c.KEY}Clés supprimées {c.RESET}: {c.RED}{summary['deleted']}{c.RESET}")
            print(f"{c.KEY}Clés inchangées {c.RESET}: {c.DIM}{summary['unchanged']}{c.RESET}")
            print(c.success(f"Fichiers générés dans: {c.VALUE}{output_dir}{c.RESET}"))

        except Exception as e:
            print(c.error(f"Erreur: {e}"))
            sys.exit(1)
    
    elif args.command == 'extract':
        try:
            print(f"{c.INFO}[INFO]{c.RESET} Extraction...")
            # Determiner le dossier UPDATE
            update_dir = args.update
            if not update_dir and hasattr(args, 'plugin_path') and args.plugin_path:
                update_dir = find_latest_tool_output(args.plugin_path, "TranslationManager")
                if not update_dir:
                    print(c.error("Aucun dossier TranslationManager trouvé dans __i18n_tmp__/"))
                    print(f"{c.DIM}        Lancez d'abord la commande 'compare'.{c.RESET}")
                    sys.exit(1)
                print(f"{c.INFO}[INFO]{c.RESET} Auto-détection: {c.VALUE}{update_dir}{c.RESET}")

            if not update_dir:
                print(c.error("--update ou --plugin-path requis"))
                sys.exit(1)

            output_dir = args.output
            if args.lang:
                output_file = run_extract(update_dir, args.lang, args.locales, output_dir)
                print(c.success(f"Généré: {c.VALUE}{output_file}{c.RESET}"))
            else:
                generated = run_extract_all(update_dir, args.locales, output_dir)
                print(f"\n{c.OK}[OK]{c.RESET} {c.WHITE}{len(generated)}{c.RESET} fichier(s) généré(s):")
                for f in generated:
                    print(f"  {c.DIM}-{c.RESET} {c.VALUE}{os.path.basename(f)}{c.RESET}")

        except Exception as e:
            print(c.error(f"Erreur: {e}"))
            sys.exit(1)
    
    elif args.command == 'inject':
        try:
            # Auto-detection du dossier translate si plugin_path fourni
            translate_dir = args.translate_dir
            update_dir = args.update
            if hasattr(args, 'plugin_path') and args.plugin_path and not translate_dir:
                translate_dir = find_latest_tool_output(args.plugin_path, "TranslationManager")
                update_dir = update_dir or translate_dir
                if translate_dir:
                    print(f"{c.INFO}[INFO]{c.RESET} Auto-détection: {c.VALUE}{translate_dir}{c.RESET}")

            if args.translate and args.target:
                print(f"{c.INFO}[INFO]{c.RESET} Injection...")
                stats = run_inject(args.translate, args.target, update_dir)
                print(c.success(f"{c.GREEN}{stats['injected']}{c.RESET} traduites + {c.CYAN}{stats['from_en']}{c.RESET} EN par défaut"))
            elif translate_dir and args.locales:
                print(f"{c.INFO}[INFO]{c.RESET} Injection...")
                results = run_inject_from_dir(translate_dir, args.locales, update_dir)
                for lang, stats in sorted(results.items()):
                    if 'error' in stats:
                        print(f"{c.CYAN}[{lang.upper()}]{c.RESET} {c.ERROR}[ERREUR]{c.RESET}: {stats['error']}")
                    else:
                        print(f"{c.CYAN}[{lang.upper()}]{c.RESET} {c.OK}[OK]{c.RESET}: {c.GREEN}{stats['injected']}{c.RESET} traduites + {c.CYAN}{stats['from_en']}{c.RESET} EN")
            else:
                print(c.error("Spécifiez --translate + --target OU --translate-dir + --locales OU --plugin-path + --locales"))
                sys.exit(1)

        except Exception as e:
            print(c.error(f"Erreur: {e}"))
            sys.exit(1)
    
    elif args.command == 'sync':
        try:
            # Auto-detection du dossier update si plugin_path fourni
            update_dir = args.update
            if hasattr(args, 'plugin_path') and args.plugin_path and not update_dir:
                update_dir = find_latest_tool_output(args.plugin_path, "TranslationManager")
                if update_dir:
                    print(f"{c.INFO}[INFO]{c.RESET} Auto-détection: {c.VALUE}{update_dir}{c.RESET}")

            if not args.ref and not update_dir:
                print(c.error("--ref, --update ou --plugin-path requis"))
                sys.exit(1)

            print(f"{c.INFO}[INFO]{c.RESET} Synchronisation...")
            results = run_sync(args.ref, args.locales, update_dir)

            if not results:
                print(c.warning("Aucune langue étrangère trouvée."))
            else:
                print()
                print(generate_sync_report(results))

        except Exception as e:
            print(c.error(f"Erreur: {e}"))
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
