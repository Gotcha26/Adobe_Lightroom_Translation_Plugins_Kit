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

Mode CLI (avec --plugin-path pour structure __i18n_kit__):
    python TranslationManager.py compare --old ancien.txt --new nouveau.txt --plugin-path ./plugin.lrplugin
    python TranslationManager.py extract --plugin-path ./plugin.lrplugin --locales ./Locales
    python TranslationManager.py inject --plugin-path ./plugin.lrplugin --locales ./Locales
    python TranslationManager.py sync --plugin-path ./plugin.lrplugin --locales ./Locales

Mode CLI (legacy):
    python TranslationManager.py compare --old ancien.txt --new nouveau.txt
    python TranslationManager.py extract --update ./20260128_143000 --locales ./Locales
    python TranslationManager.py inject --translate-dir ./20260128_143000 --locales ./Locales
    python TranslationManager.py sync --update ./20260128_143000 --locales ./Locales

Sorties generees dans: <plugin>/__i18n_kit__/TranslationManager/<timestamp>/

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-01-29
Version: 5.0 - Structure __i18n_kit__ avec auto-detection
"""

import os
import sys
import argparse

# Ajouter le répertoire courant et parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.paths import get_tool_output_path, find_latest_tool_output

from TM_common import clear_screen, print_header
from TM_compare import run_compare, menu_compare
from TM_extract import run_extract, run_extract_all, menu_extract
from TM_inject import run_inject, run_inject_from_dir, menu_inject
from TM_sync import run_sync, generate_sync_report, menu_sync


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def main_menu():
    """Menu principal interactif."""
    while True:
        clear_screen()
        print_header()
        
        print("\n  Options:")
        print("  " + "-" * 66)
        print("  1. COMPARE")
        print("     Compare ancien EN vs nouveau EN")
        print("     → Génère UPDATE_en.json + CHANGELOG.txt")
        print()
        print("  2. EXTRACT (optionnel)")
        print("     Génère mini fichiers TRANSLATE_xx.txt pour traduction")
        print()
        print("  3. INJECT (optionnel)")
        print("     Réinjecte les traductions (EN par défaut si vide)")
        print()
        print("  4. SYNC")
        print("     Met à jour les langues avec EN")
        print("     → Ajoute [NEW], marque [NEEDS_REVIEW], supprime obsolètes")
        print()
        print("  5. Aide")
        print()
        print("  0. Quitter")
        print("  " + "-" * 66)
        
        choice = input("\n  Votre choix (0-5): ").strip()
        
        if choice == '1':
            menu_compare()
            input("\n  Appuyez sur Entrée pour continuer...")
        elif choice == '2':
            menu_extract()
            input("\n  Appuyez sur Entrée pour continuer...")
        elif choice == '3':
            menu_inject()
        elif choice == '4':
            menu_sync()
        elif choice == '5':
            clear_screen()
            print(__doc__)
            input("\nAppuyez sur Entrée pour revenir au menu...")
        elif choice == '0':
            print("\n  👋 Au revoir!")
            break
        else:
            input("\n  ❌ Choix invalide. Appuyez sur Entrée...")


# =============================================================================
# CLI
# =============================================================================

def main():
    """Point d'entrée principal."""
    
    if len(sys.argv) == 1:
        main_menu()
        return
    
    parser = argparse.ArgumentParser(
        description="Gestionnaire de traductions multilingues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Mode interactif
  python TranslationManager.py

  # Avec --plugin-path (structure __i18n_kit__):
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
    compare_parser.add_argument('--plugin-path', help='Chemin plugin (sortie: __i18n_kit__/TranslationManager/)')
    compare_parser.add_argument('--output', help='Override repertoire de sortie')
    
    # extract
    extract_parser = subparsers.add_parser('extract', help='Genere fichiers TRANSLATE_*.txt')
    extract_parser.add_argument('--update', help='Dossier UPDATE (ou auto-detection si --plugin-path)')
    extract_parser.add_argument('--plugin-path', help='Chemin plugin (auto-detection __i18n_kit__/)')
    extract_parser.add_argument('--locales', help='Repertoire des traductions existantes')
    extract_parser.add_argument('--lang', help='Langue specifique (defaut: toutes)')
    extract_parser.add_argument('--output', help='Override repertoire de sortie')
    
    # inject
    inject_parser = subparsers.add_parser('inject', help='Injecte les traductions')
    inject_parser.add_argument('--translate', help='Fichier TRANSLATE_xx.txt')
    inject_parser.add_argument('--target', help='Fichier TranslatedStrings_xx.txt cible')
    inject_parser.add_argument('--translate-dir', help='Dossier contenant TRANSLATE_*.txt')
    inject_parser.add_argument('--plugin-path', help='Chemin plugin (auto-detection __i18n_kit__/)')
    inject_parser.add_argument('--locales', help='Dossier des fichiers de langue')
    inject_parser.add_argument('--update', help='Dossier UPDATE (pour valeurs EN)')
    
    # sync
    sync_parser = subparsers.add_parser('sync', help='Synchronise les langues')
    sync_parser.add_argument('--ref', help='Fichier EN de reference')
    sync_parser.add_argument('--plugin-path', help='Chemin plugin (auto-detection __i18n_kit__/)')
    sync_parser.add_argument('--locales', help='Repertoire des fichiers de langues')
    sync_parser.add_argument('--update', help='Dossier UPDATE (avec UPDATE_en.json)')
    
    args = parser.parse_args()
    
    if args.command == 'compare':
        try:
            print("Comparaison...")
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
            print(f"\n{'=' * 60}")
            print("RÉSUMÉ")
            print(f"{'=' * 60}")
            print(f"Clés ajoutées    : {summary['added']}")
            print(f"Clés modifiées   : {summary['changed']}")
            print(f"Clés supprimées  : {summary['deleted']}")
            print(f"Clés inchangées  : {summary['unchanged']}")
            print(f"\n✓ Fichiers générés dans: {output_dir}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            sys.exit(1)
    
    elif args.command == 'extract':
        try:
            print("Extraction...")
            # Determiner le dossier UPDATE
            update_dir = args.update
            if not update_dir and hasattr(args, 'plugin_path') and args.plugin_path:
                update_dir = find_latest_tool_output(args.plugin_path, "TranslationManager")
                if not update_dir:
                    print("ERREUR: Aucun dossier TranslationManager trouve dans __i18n_kit__/")
                    print("        Lancez d'abord la commande 'compare'.")
                    sys.exit(1)
                print(f"* Auto-detection: {update_dir}")

            if not update_dir:
                print("ERREUR: --update ou --plugin-path requis")
                sys.exit(1)

            output_dir = args.output
            if args.lang:
                output_file = run_extract(update_dir, args.lang, args.locales, output_dir)
                print(f"[OK] Genere: {output_file}")
            else:
                generated = run_extract_all(update_dir, args.locales, output_dir)
                print(f"\n[OK] {len(generated)} fichier(s) genere(s):")
                for f in generated:
                    print(f"  - {os.path.basename(f)}")

        except Exception as e:
            print(f"ERREUR: {e}")
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
                    print(f"* Auto-detection: {translate_dir}")

            if args.translate and args.target:
                print("Injection...")
                stats = run_inject(args.translate, args.target, update_dir)
                print(f"[OK] {stats['injected']} traduites + {stats['from_en']} EN par defaut")
            elif translate_dir and args.locales:
                print("Injection...")
                results = run_inject_from_dir(translate_dir, args.locales, update_dir)
                for lang, stats in sorted(results.items()):
                    if 'error' in stats:
                        print(f"[{lang.upper()}] ERREUR: {stats['error']}")
                    else:
                        print(f"[{lang.upper()}] OK: {stats['injected']} traduites + {stats['from_en']} EN")
            else:
                print("ERREUR: Specifiez --translate + --target OU --translate-dir + --locales OU --plugin-path + --locales")
                sys.exit(1)

        except Exception as e:
            print(f"ERREUR: {e}")
            sys.exit(1)
    
    elif args.command == 'sync':
        try:
            # Auto-detection du dossier update si plugin_path fourni
            update_dir = args.update
            if hasattr(args, 'plugin_path') and args.plugin_path and not update_dir:
                update_dir = find_latest_tool_output(args.plugin_path, "TranslationManager")
                if update_dir:
                    print(f"* Auto-detection: {update_dir}")

            if not args.ref and not update_dir:
                print("ERREUR: --ref, --update ou --plugin-path requis")
                sys.exit(1)

            print("Synchronisation...")
            results = run_sync(args.ref, args.locales, update_dir)

            if not results:
                print("ATTENTION: Aucune langue etrangere trouvee.")
            else:
                print()
                print(generate_sync_report(results))

        except Exception as e:
            print(f"ERREUR: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
