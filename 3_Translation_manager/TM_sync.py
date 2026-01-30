#!/usr/bin/env python3
"""
TM_sync.py

Module SYNC pour TranslationManager.
Synchronise les langues étrangères avec le fichier EN de référence.
"""

import os
import shutil
from datetime import datetime
from typing import Dict, List, Set, Optional

from TM_common import (
    parse_translation_file, write_translation_file, 
    resolve_path, load_update_json, find_languages
)


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_sync(reference_path: str = None, locales_dir: str = None, 
             update_dir: str = None) -> Dict[str, Dict]:
    """
    Synchronise les langues étrangères avec le fichier EN.
    
    Modes:
        1. Avec --update: utilise UPDATE_en.json pour marquer les changements
        2. Sans --update: synchronisation simple des clés
    
    Args:
        reference_path: Fichier EN de référence (ou répertoire)
        locales_dir: Répertoire des fichiers de langues
        update_dir: Répertoire contenant UPDATE_en.json (optionnel)
    
    Returns:
        Dict par langue avec les statistiques
    """
    # Charger les données de mise à jour si disponibles
    update_data = None
    if update_dir:
        update_data = load_update_json(update_dir)
        # Utiliser le fichier EN du dossier update comme référence
        ref_in_update = os.path.join(update_dir, 'TranslatedStrings_en.txt')
        if os.path.isfile(ref_in_update):
            reference_path = ref_in_update
    
    # Résoudre le chemin de référence
    if not reference_path:
        raise ValueError("Chemin de référence EN requis (--ref ou via --update)")
    
    ref_dir, ref_file = resolve_path(reference_path)
    
    # Déterminer le répertoire des locales
    if not locales_dir:
        locales_dir = ref_dir
    
    # Charger le fichier EN de référence
    en_strings = parse_translation_file(ref_file)
    en_keys = set(en_strings.keys())
    
    # Trouver les langues étrangères
    other_languages = find_languages(locales_dir, exclude_en=True)
    
    if not other_languages:
        return {}
    
    # Préparer les infos de changement depuis update_data
    added_keys = set()
    changed_keys = set()
    deleted_keys = set()
    
    if update_data:
        added_keys = set(update_data.get('added', {}).keys())
        changed_keys = set(update_data.get('changed', {}).keys())
        deleted_keys = set(update_data.get('deleted', []))
    
    results = {}
    
    for lang in sorted(other_languages):
        lang_file = os.path.join(locales_dir, f'TranslatedStrings_{lang}.txt')
        result = _sync_language(
            lang, lang_file, en_strings, en_keys,
            added_keys, changed_keys, deleted_keys,
            locales_dir, update_data
        )
        results[lang] = result
    
    return results


def _sync_language(lang: str, lang_file: str, en_strings: Dict[str, str],
                   en_keys: Set[str], added_keys: Set[str], changed_keys: Set[str],
                   deleted_keys: Set[str], output_dir: str,
                   update_data: Dict = None) -> Dict:
    """Synchronise une langue avec le fichier EN."""
    
    # Charger la langue actuelle
    if os.path.isfile(lang_file):
        lang_strings = parse_translation_file(lang_file)
        # Créer backup
        shutil.copy2(lang_file, lang_file + '.bak')
    else:
        lang_strings = {}
    
    lang_keys = set(lang_strings.keys())
    
    # Calculer les différences
    missing_in_lang = en_keys - lang_keys
    extra_in_lang = lang_keys - en_keys
    common_keys = en_keys & lang_keys
    
    # Construire le nouveau dictionnaire
    new_strings = {}
    markers = {}
    
    stats = {
        'kept': 0,
        'added': 0,
        'needs_review': 0,
        'removed': 0
    }
    
    # Clés communes : garder la traduction existante
    for key in common_keys:
        new_strings[key] = lang_strings[key]
        stats['kept'] += 1
        
        # Marquer si le texte EN a changé
        if key in changed_keys:
            markers[key] = f"-- ## NEEDS_REVIEW ## Texte EN modifié"
            stats['needs_review'] += 1
    
    # Clés manquantes : ajouter avec valeur EN
    for key in missing_in_lang:
        new_strings[key] = en_strings[key]  # Valeur EN par défaut
        markers[key] = f"-- ## NEW ## À traduire"
        stats['added'] += 1
    
    # Clés en trop : ne pas copier (= supprimées)
    stats['removed'] = len(extra_in_lang)
    
    # Métadonnées pour l'entête
    metadata = {
        'new_keys': stats['added'],
        'changed_keys': stats['needs_review'],
        'source': 'SYNC'
    }
    
    # Écrire le fichier
    output_file = os.path.join(output_dir, f'TranslatedStrings_{lang}.txt')
    write_translation_file(output_file, lang, new_strings, markers, metadata)
    
    return {
        'kept': stats['kept'],
        'added': stats['added'],
        'needs_review': stats['needs_review'],
        'removed': stats['removed'],
        'total': len(new_strings),
        'added_keys': sorted(list(missing_in_lang)),
        'removed_keys': sorted(list(extra_in_lang)),
        'review_keys': sorted(list(changed_keys & common_keys))
    }


def generate_sync_report(results: Dict[str, Dict]) -> str:
    """Génère un rapport de synchronisation."""
    lines = []
    lines.append("=" * 70)
    lines.append("RAPPORT DE SYNCHRONISATION")
    lines.append("=" * 70)
    lines.append("")
    
    total_added = 0
    total_review = 0
    total_removed = 0
    
    for lang, data in sorted(results.items()):
        total_added += data['added']
        total_review += data['needs_review']
        total_removed += data['removed']
        
        lines.append(f"[{lang.upper()}]")
        lines.append(f"  Clés conservées   : {data['kept']}")
        lines.append(f"  Clés ajoutées     : {data['added']}  [NEW] à traduire")
        lines.append(f"  Clés à réviser    : {data['needs_review']}  [NEEDS_REVIEW]")
        lines.append(f"  Clés supprimées   : {data['removed']}")
        lines.append(f"  Total             : {data['total']}")
        
        if data['added_keys']:
            lines.append(f"  Nouvelles clés:")
            for key in data['added_keys'][:5]:
                lines.append(f"    + {key}")
            if len(data['added_keys']) > 5:
                lines.append(f"    ... et {len(data['added_keys']) - 5} autres")
        
        if data['review_keys']:
            lines.append(f"  Clés à réviser:")
            for key in data['review_keys'][:5]:
                lines.append(f"    ? {key}")
            if len(data['review_keys']) > 5:
                lines.append(f"    ... et {len(data['review_keys']) - 5} autres")
        
        lines.append("")
    
    lines.append("-" * 70)
    lines.append("TOTAL")
    lines.append("-" * 70)
    lines.append(f"  Langues traitées  : {len(results)}")
    lines.append(f"  Clés ajoutées     : {total_added}")
    lines.append(f"  Clés à réviser    : {total_review}")
    lines.append(f"  Clés supprimées   : {total_removed}")
    
    return "\n".join(lines)


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_sync():
    """Menu interactif pour SYNC."""
    from TM_common import clear_screen, print_header
    
    clear_screen()
    print_header()
    print("\n  SYNC: Synchroniser les langues étrangères")
    print("  " + "-" * 66)
    
    print("\n  Avez-vous un dossier UPDATE (généré par COMPARE) ?")
    print("  (Permet de marquer les clés [NEEDS_REVIEW])")
    has_update = input("  [O/n]: ").strip().lower()
    
    update_dir = None
    ref_path = None
    locales_dir = None
    
    if has_update in ['o', 'y', '', 'oui', 'yes']:
        print("\n  Dossier UPDATE (contenant UPDATE_en.json):")
        update_dir = input("  > ").strip()
        if not update_dir or not os.path.isdir(update_dir):
            input(f"\n  ❌ Répertoire invalide.\n  Appuyez sur Entrée...")
            return None
    else:
        print("\n  Fichier EN de référence (ou répertoire):")
        ref_path = input("  > ").strip()
        if not ref_path:
            input("\n  ❌ Chemin requis.\n  Appuyez sur Entrée...")
            return None
    
    print("\n  Répertoire des fichiers de langues (Locales):")
    print("  (Entrée = même répertoire que la référence)")
    locales_dir = input("  > ").strip() or None
    
    try:
        print("\n  Synchronisation en cours...")
        results = run_sync(ref_path, locales_dir, update_dir)
        
        if not results:
            print("\n  ⚠️  Aucune langue étrangère trouvée.")
        else:
            print()
            print(generate_sync_report(results))
            print()
            print("  ✓ Fichiers mis à jour (backups .bak créés)")
            print()
            print("  PROCHAINE ÉTAPE:")
            print("  Recherchez [NEW] et [NEEDS_REVIEW] dans les fichiers")
            print("  pour compléter les traductions.")
        
        return results
        
    except FileNotFoundError as e:
        print(f"\n  ❌ Fichier non trouvé: {e}")
    except Exception as e:
        print(f"\n  ❌ Erreur: {e}")
    
    input("\n  Appuyez sur Entrée pour continuer...")
    return None
