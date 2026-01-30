#!/usr/bin/env python3
"""
TM_inject.py

Module INJECT pour TranslationManager.
Réinjecte les traductions depuis TRANSLATE_xx.txt dans les fichiers de langue.

IMPORTANT: Les clés non traduites (→ vide) reçoivent la valeur EN par défaut.
"""

import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional

from TM_common import (
    parse_translation_file, write_translation_file, 
    load_update_json, find_languages
)


# =============================================================================
# PARSER TRANSLATE
# =============================================================================

def parse_translate_file(file_path: str, update_data: Dict = None) -> Dict[str, str]:
    """
    Parse un fichier TRANSLATE_xx.txt et extrait les traductions.
    
    IMPORTANT: 
    - Si une traduction est fournie après → : on l'utilise
    - Si → est vide : on utilise la valeur EN depuis update_data
    
    Args:
        file_path: Chemin du fichier TRANSLATE_xx.txt
        update_data: Données UPDATE_en.json pour récupérer les valeurs EN
    
    Returns:
        Dict[str, str]: {clé: traduction}
    """
    translations = {}
    current_key = None
    current_en_value = None
    
    # Préparer les valeurs EN depuis update_data
    en_values = {}
    if update_data:
        # Clés ajoutées
        for key, value in update_data.get('added', {}).items():
            en_values[key] = value
        # Clés modifiées (nouvelle valeur EN)
        for key, change in update_data.get('changed', {}).items():
            en_values[key] = change.get('new', '')
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n\r')
            
            # Ignorer les commentaires et lignes vides
            if line.startswith('#') or not line.strip():
                continue
            
            # Détecter la clé
            if line.startswith('[KEY]'):
                current_key = line.replace('[KEY]', '').strip()
                current_en_value = en_values.get(current_key, '')
            
            # Détecter la valeur EN (pour les clés non dans update_data)
            elif line.startswith('[EN]') and not line.startswith('[EN '):
                if current_key and not current_en_value:
                    current_en_value = line.replace('[EN]', '').strip()
            
            # Détecter [EN APRÈS] pour les clés modifiées
            elif line.startswith('[EN APRÈS]'):
                if current_key:
                    current_en_value = line.replace('[EN APRÈS]', '').strip()
            
            # Détecter la traduction (ligne avec →)
            elif '] → ' in line or '] →' in line:
                parts = line.split('→', 1)
                if len(parts) == 2 and current_key:
                    translation = parts[1].strip()
                    
                    if translation:
                        # Traduction fournie
                        translations[current_key] = translation
                    else:
                        # Pas de traduction → utiliser valeur EN
                        translations[current_key] = current_en_value or ''
    
    return translations


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_inject(translate_file: str, target_file: str, 
               update_dir: str = None, create_backup: bool = True) -> Dict:
    """
    Injecte les traductions d'un fichier TRANSLATE dans un fichier de langue.
    
    Args:
        translate_file: Fichier TRANSLATE_xx.txt avec les traductions
        target_file: Fichier TranslatedStrings_xx.txt cible
        update_dir: Répertoire contenant UPDATE_en.json (pour valeurs EN par défaut)
        create_backup: Créer une sauvegarde .bak
    
    Returns:
        Statistiques d'injection
    """
    # Charger UPDATE_en.json si disponible
    update_data = None
    if update_dir:
        update_data = load_update_json(update_dir)
    else:
        # Essayer de trouver UPDATE_en.json dans le même dossier que TRANSLATE
        translate_dir = os.path.dirname(translate_file)
        update_data = load_update_json(translate_dir)
    
    # Parser le fichier de traduction
    new_translations = parse_translate_file(translate_file, update_data)
    
    if not new_translations:
        return {'injected': 0, 'from_en': 0, 'skipped': 0, 'total': 0}
    
    # Charger le fichier cible existant
    if os.path.isfile(target_file):
        existing = parse_translation_file(target_file)
        if create_backup:
            shutil.copy2(target_file, target_file + '.bak')
    else:
        existing = {}
    
    # Fusionner
    stats = {'injected': 0, 'from_en': 0, 'skipped': 0}
    
    # Récupérer les valeurs EN pour comparaison
    en_values = {}
    if update_data:
        for key, value in update_data.get('added', {}).items():
            en_values[key] = value
        for key, change in update_data.get('changed', {}).items():
            en_values[key] = change.get('new', '')
    
    for key, translation in new_translations.items():
        if translation:
            # Vérifier si c'est la valeur EN ou une vraie traduction
            if key in en_values and translation == en_values[key]:
                stats['from_en'] += 1
            else:
                stats['injected'] += 1
            existing[key] = translation
        else:
            stats['skipped'] += 1
    
    stats['total'] = len(existing)
    
    # Détecter la langue depuis le nom du fichier
    lang = 'xx'
    basename = os.path.basename(target_file)
    if 'TranslatedStrings_' in basename:
        lang = basename.replace('TranslatedStrings_', '').replace('.txt', '')
    
    # Métadonnées pour l'entête
    metadata = {
        'new_keys': stats['injected'] + stats['from_en'],
        'source': os.path.basename(translate_file)
    }
    
    # Écrire le fichier mis à jour
    write_translation_file(target_file, lang, existing, metadata=metadata)
    
    return stats


def run_inject_from_dir(translate_dir: str, locales_dir: str,
                        update_dir: str = None,
                        create_backup: bool = True) -> Dict[str, Dict]:
    """
    Injecte tous les fichiers TRANSLATE_*.txt dans les fichiers de langue.
    
    Args:
        translate_dir: Répertoire contenant les fichiers TRANSLATE_*.txt
        locales_dir: Répertoire des fichiers TranslatedStrings_*.txt
        update_dir: Répertoire UPDATE (défaut: translate_dir)
        create_backup: Créer des sauvegardes .bak
    
    Returns:
        Statistiques par langue
    """
    if not update_dir:
        update_dir = translate_dir
    
    results = {}
    
    # Trouver tous les fichiers TRANSLATE_*.txt
    for file in os.listdir(translate_dir):
        if file.startswith('TRANSLATE_') and file.endswith('.txt'):
            lang = file.replace('TRANSLATE_', '').replace('.txt', '')
            
            translate_file = os.path.join(translate_dir, file)
            target_file = os.path.join(locales_dir, f'TranslatedStrings_{lang}.txt')
            
            try:
                stats = run_inject(translate_file, target_file, update_dir, create_backup)
                results[lang] = stats
            except Exception as e:
                results[lang] = {'error': str(e)}
    
    return results


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_inject():
    """Menu interactif pour INJECT."""
    from TM_common import clear_screen, print_header
    
    clear_screen()
    print_header()
    print("\n  INJECT: Réinjecter les traductions")
    print("  " + "-" * 66)
    print("\n  Note: Les clés non traduites (→ vide) recevront la valeur EN")
    
    print("\n  Mode:")
    print("  1. Injecter un fichier TRANSLATE_xx.txt spécifique")
    print("  2. Injecter tous les fichiers TRANSLATE_*.txt d'un dossier")
    mode = input("\n  Choix (1-2): ").strip()
    
    if mode == '1':
        print("\n  Fichier TRANSLATE_xx.txt:")
        translate_file = input("  > ").strip()
        if not translate_file or not os.path.isfile(translate_file):
            input("\n  ❌ Fichier invalide.\n  Appuyez sur Entrée...")
            return None
        
        print("\n  Fichier cible TranslatedStrings_xx.txt:")
        target_file = input("  > ").strip()
        if not target_file:
            input("\n  ❌ Chemin requis.\n  Appuyez sur Entrée...")
            return None
        
        print("\n  Dossier UPDATE (contenant UPDATE_en.json):")
        print("  (Entrée = même dossier que TRANSLATE)")
        update_dir = input("  > ").strip() or None
        
        try:
            print("\n  Injection en cours...")
            stats = run_inject(translate_file, target_file, update_dir)
            
            print("\n  " + "=" * 66)
            print("  RÉSULTAT")
            print("  " + "=" * 66)
            print(f"  Traductions injectées   : {stats['injected']}")
            print(f"  Valeurs EN par défaut   : {stats['from_en']}")
            print(f"  Entrées ignorées        : {stats['skipped']}")
            print(f"  Total clés dans fichier : {stats['total']}")
            print()
            print(f"  ✓ Fichier mis à jour: {target_file}")
            print("  (Backup .bak créé)")
            
            return stats
            
        except Exception as e:
            print(f"\n  ❌ Erreur: {e}")
    
    elif mode == '2':
        print("\n  Dossier contenant les fichiers TRANSLATE_*.txt:")
        translate_dir = input("  > ").strip()
        if not translate_dir or not os.path.isdir(translate_dir):
            input("\n  ❌ Répertoire invalide.\n  Appuyez sur Entrée...")
            return None
        
        print("\n  Répertoire des fichiers de langue (Locales):")
        locales_dir = input("  > ").strip()
        if not locales_dir or not os.path.isdir(locales_dir):
            input("\n  ❌ Répertoire invalide.\n  Appuyez sur Entrée...")
            return None
        
        print("\n  Dossier UPDATE (contenant UPDATE_en.json):")
        print("  (Entrée = même dossier que TRANSLATE)")
        update_dir = input("  > ").strip() or None
        
        try:
            print("\n  Injection en cours...")
            results = run_inject_from_dir(translate_dir, locales_dir, update_dir)
            
            if results:
                print("\n  " + "=" * 66)
                print("  RÉSULTAT")
                print("  " + "=" * 66)
                for lang, stats in sorted(results.items()):
                    if 'error' in stats:
                        print(f"  [{lang.upper()}] ❌ {stats['error']}")
                    else:
                        translated = stats['injected']
                        from_en = stats['from_en']
                        print(f"  [{lang.upper()}] ✓ {translated} traduites + {from_en} EN par défaut")
                print()
                print("  ✓ Fichiers mis à jour (backups .bak créés)")
                
                return results
            else:
                print("\n  ⚠️  Aucun fichier TRANSLATE_*.txt trouvé")
            
        except Exception as e:
            print(f"\n  ❌ Erreur: {e}")
    
    else:
        input("\n  ❌ Choix invalide.\n  Appuyez sur Entrée...")
        return None
    
    input("\n  Appuyez sur Entrée pour continuer...")
    return None
