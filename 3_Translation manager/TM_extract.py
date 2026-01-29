#!/usr/bin/env python3
"""
TM_extract.py

Module EXTRACT pour TranslationManager.
Génère les fichiers TRANSLATE_xx.txt pour faciliter la traduction.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from TM_common import parse_translation_file, load_update_json, find_languages


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_extract(update_dir: str, lang: str, locales_dir: str = None,
                output_dir: str = None) -> str:
    """
    Génère un fichier TRANSLATE_xx.txt avec les clés à traduire.
    
    Args:
        update_dir: Répertoire contenant UPDATE_en.json
        lang: Code langue cible (fr, de, es...)
        locales_dir: Répertoire des fichiers de langues existants
        output_dir: Répertoire de sortie (défaut: update_dir)
    
    Returns:
        Chemin du fichier généré
    """
    # Charger UPDATE_en.json
    update_data = load_update_json(update_dir)
    if not update_data:
        raise FileNotFoundError(f"UPDATE_en.json non trouvé dans: {update_dir}")
    
    # Charger les traductions existantes si disponibles
    existing_translations = {}
    if locales_dir:
        existing_file = os.path.join(locales_dir, f'TranslatedStrings_{lang}.txt')
        if os.path.isfile(existing_file):
            existing_translations = parse_translation_file(existing_file)
    
    # Répertoire de sortie
    if not output_dir:
        output_dir = update_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Générer le fichier TRANSLATE
    output_file = os.path.join(output_dir, f'TRANSLATE_{lang}.txt')
    
    added_keys = update_data.get('added', {})
    changed_keys = update_data.get('changed', {})
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# " + "=" * 70 + "\n")
        f.write(f"# FICHIER DE TRADUCTION - {lang.upper()}\n")
        f.write(f"# Généré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Source: {update_dir}\n")
        f.write("# " + "=" * 70 + "\n")
        f.write("#\n")
        f.write("# INSTRUCTIONS:\n")
        f.write("# 1. Pour chaque entrée, écrivez la traduction après le symbole →\n")
        f.write("# 2. Laissez vide pour garder la valeur EN par défaut\n")
        f.write("# 3. Les lignes commençant par # sont ignorées\n")
        f.write("#\n")
        f.write("# " + "=" * 70 + "\n\n")
        
        # Section: Nouvelles clés
        if added_keys:
            f.write("# " + "-" * 70 + "\n")
            f.write(f"# NOUVELLES CLÉS ({len(added_keys)})\n")
            f.write("# " + "-" * 70 + "\n\n")
            
            for key in sorted(added_keys.keys()):
                en_value = added_keys[key]
                f.write(f"[KEY] {key}\n")
                f.write(f"[EN]  {en_value}\n")
                f.write(f"[{lang.upper()}] → \n")
                f.write("\n")
        
        # Section: Clés modifiées
        if changed_keys:
            f.write("# " + "-" * 70 + "\n")
            f.write(f"# CLÉS MODIFIÉES ({len(changed_keys)}) - Le texte EN a changé\n")
            f.write("# " + "-" * 70 + "\n\n")
            
            for key in sorted(changed_keys.keys()):
                change = changed_keys[key]
                old_en = change['old']
                new_en = change['new']
                current_trans = existing_translations.get(key, '')
                
                f.write(f"[KEY] {key}\n")
                f.write(f"[EN AVANT]  {old_en}\n")
                f.write(f"[EN APRÈS]  {new_en}\n")
                if current_trans and current_trans != old_en:
                    f.write(f"[{lang.upper()} ACTUEL] {current_trans}\n")
                f.write(f"[{lang.upper()}] → \n")
                f.write("\n")
        
        # Résumé
        f.write("# " + "=" * 70 + "\n")
        f.write(f"# TOTAL: {len(added_keys)} nouvelles + {len(changed_keys)} modifiées\n")
        f.write("# " + "=" * 70 + "\n")
    
    return output_file


def run_extract_all(update_dir: str, locales_dir: str = None,
                    output_dir: str = None) -> List[str]:
    """
    Génère les fichiers TRANSLATE pour toutes les langues détectées.
    
    Args:
        update_dir: Répertoire contenant UPDATE_en.json
        locales_dir: Répertoire des fichiers de langues existants
        output_dir: Répertoire de sortie
    
    Returns:
        Liste des fichiers générés
    """
    # Trouver les langues existantes
    languages = []
    
    if locales_dir and os.path.isdir(locales_dir):
        languages = find_languages(locales_dir, exclude_en=True)
    
    # Si aucune langue trouvée, proposer français par défaut
    if not languages:
        languages = ['fr']
    
    generated_files = []
    for lang in sorted(languages):
        try:
            output_file = run_extract(update_dir, lang, locales_dir, output_dir)
            generated_files.append(output_file)
        except Exception as e:
            print(f"  ⚠️  Erreur pour {lang}: {e}")
    
    return generated_files


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_extract():
    """Menu interactif pour EXTRACT."""
    from TM_common import clear_screen, print_header, load_update_json
    
    clear_screen()
    print_header()
    print("\n  EXTRACT: Générer fichiers de traduction")
    print("  " + "-" * 66)
    
    print("\n  Dossier UPDATE (contenant UPDATE_en.json):")
    update_dir = input("  > ").strip()
    if not update_dir or not os.path.isdir(update_dir):
        input("\n  ❌ Répertoire invalide.\n  Appuyez sur Entrée...")
        return None
    
    # Vérifier UPDATE_en.json
    if not load_update_json(update_dir):
        input("\n  ❌ UPDATE_en.json non trouvé.\n  Appuyez sur Entrée...")
        return None
    
    print("\n  Répertoire des traductions existantes (Locales):")
    print("  (Pour récupérer les traductions actuelles des clés modifiées)")
    print("  (Entrée pour ignorer)")
    locales_dir = input("  > ").strip() or None
    
    print("\n  Langue(s) à générer:")
    print("  • Entrée = toutes les langues trouvées dans Locales")
    print("  • Ou spécifier: fr, de, es...")
    lang_input = input("  > ").strip().lower()
    
    try:
        print("\n  Génération en cours...")
        
        if lang_input:
            languages = [l.strip() for l in lang_input.split(',')]
            generated = []
            for lang in languages:
                output_file = run_extract(update_dir, lang, locales_dir)
                generated.append(output_file)
        else:
            generated = run_extract_all(update_dir, locales_dir)
        
        if generated:
            print("\n  " + "=" * 66)
            print("  FICHIERS GÉNÉRÉS")
            print("  " + "=" * 66)
            for f in generated:
                print(f"  ✓ {os.path.basename(f)}")
            print()
            print("  PROCHAINE ÉTAPE:")
            print("  1. Éditez les fichiers et remplissez après chaque →")
            print("  2. Lancez INJECT pour réinjecter les traductions")
            print("  3. Lancez SYNC pour finaliser")
            
            return generated
        else:
            print("\n  ⚠️  Aucun fichier généré")
        
    except Exception as e:
        print(f"\n  ❌ Erreur: {e}")
    
    input("\n  Appuyez sur Entrée pour continuer...")
    return None
