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

Mode CLI:
    python TranslationManager.py compare --old ancien.txt --new nouveau.txt
    python TranslationManager.py extract --update ./20260128_143000 --locales ./Locales
    python TranslationManager.py inject --translate-dir ./20260128_143000 --locales ./Locales
    python TranslationManager.py sync --update ./20260128_143000 --locales ./Locales

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-01-28
Version: 4.2
"""

import os
import sys
import argparse

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
  
  # Comparer deux versions EN
  python TranslationManager.py compare --old ./v1/en.txt --new ./v2/en.txt
  
  # Extraire les clés à traduire
  python TranslationManager.py extract --update ./20260128_143000 --locales ./Locales
  
  # Injecter les traductions
  python TranslationManager.py inject --translate-dir ./20260128_143000 --locales ./Locales
  
  # Synchroniser avec un dossier UPDATE
  python TranslationManager.py sync --update ./20260128_143000 --locales ./Locales
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commande')
    
    # compare
    compare_parser = subparsers.add_parser('compare', help='Compare deux versions EN')
    compare_parser.add_argument('--old', required=True, help='Ancien fichier EN')
    compare_parser.add_argument('--new', required=True, help='Nouveau fichier EN')
    compare_parser.add_argument('--output', help='Répertoire de sortie')
    
    # extract
    extract_parser = subparsers.add_parser('extract', help='Génère fichiers TRANSLATE_*.txt')
    extract_parser.add_argument('--update', required=True, help='Dossier UPDATE')
    extract_parser.add_argument('--locales', help='Répertoire des traductions existantes')
    extract_parser.add_argument('--lang', help='Langue spécifique (défaut: toutes)')
    extract_parser.add_argument('--output', help='Répertoire de sortie')
    
    # inject
    inject_parser = subparsers.add_parser('inject', help='Injecte les traductions')
    inject_parser.add_argument('--translate', help='Fichier TRANSLATE_xx.txt')
    inject_parser.add_argument('--target', help='Fichier TranslatedStrings_xx.txt cible')
    inject_parser.add_argument('--translate-dir', help='Dossier contenant TRANSLATE_*.txt')
    inject_parser.add_argument('--locales', help='Dossier des fichiers de langue')
    inject_parser.add_argument('--update', help='Dossier UPDATE (pour valeurs EN)')
    
    # sync
    sync_parser = subparsers.add_parser('sync', help='Synchronise les langues')
    sync_parser.add_argument('--ref', help='Fichier EN de référence')
    sync_parser.add_argument('--locales', help='Répertoire des fichiers de langues')
    sync_parser.add_argument('--update', help='Dossier UPDATE (avec UPDATE_en.json)')
    
    args = parser.parse_args()
    
    if args.command == 'compare':
        try:
            print("Comparaison...")
            output_dir = run_compare(args.old, args.new, args.output)
            
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
            if args.lang:
                output_file = run_extract(args.update, args.lang, args.locales, args.output)
                print(f"✓ Généré: {output_file}")
            else:
                generated = run_extract_all(args.update, args.locales, args.output)
                print(f"\n✓ {len(generated)} fichier(s) généré(s):")
                for f in generated:
                    print(f"  • {os.path.basename(f)}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            sys.exit(1)
    
    elif args.command == 'inject':
        try:
            if args.translate and args.target:
                print("Injection...")
                stats = run_inject(args.translate, args.target, args.update)
                print(f"✓ {stats['injected']} traduites + {stats['from_en']} EN par défaut")
            elif args.translate_dir and args.locales:
                print("Injection...")
                results = run_inject_from_dir(args.translate_dir, args.locales, args.update)
                for lang, stats in sorted(results.items()):
                    if 'error' in stats:
                        print(f"[{lang.upper()}] ❌ {stats['error']}")
                    else:
                        print(f"[{lang.upper()}] ✓ {stats['injected']} traduites + {stats['from_en']} EN")
            else:
                print("❌ Spécifiez --translate + --target OU --translate-dir + --locales")
                sys.exit(1)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            sys.exit(1)
    
    elif args.command == 'sync':
        try:
            if not args.ref and not args.update:
                print("❌ --ref ou --update requis")
                sys.exit(1)
            
            print("Synchronisation...")
            results = run_sync(args.ref, args.locales, args.update)
            
            if not results:
                print("⚠️  Aucune langue étrangère trouvée.")
            else:
                print()
                print(generate_sync_report(results))
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            sys.exit(1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
