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
    resolve_path, load_update_json, find_languages, c
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
    """Génère un rapport de synchronisation avec couleurs."""
    lines = []
    lines.append(f"{c.HEADER}{'=' * 70}{c.RESET}")
    lines.append(f"{c.TITLE}RAPPORT DE SYNCHRONISATION{c.RESET}")
    lines.append(f"{c.HEADER}{'=' * 70}{c.RESET}")
    lines.append("")

    total_added = 0
    total_review = 0
    total_removed = 0

    for lang, data in sorted(results.items()):
        total_added += data['added']
        total_review += data['needs_review']
        total_removed += data['removed']

        lines.append(f"{c.CYAN}[{lang.upper()}]{c.RESET}")
        lines.append(f"  {c.KEY}Clés conservées  {c.RESET}: {c.WHITE}{data['kept']}{c.RESET}")
        lines.append(f"  {c.KEY}Clés ajoutées    {c.RESET}: {c.GREEN}{data['added']}{c.RESET}  {c.DIM}[NEW] à traduire{c.RESET}")
        lines.append(f"  {c.KEY}Clés à réviser   {c.RESET}: {c.YELLOW}{data['needs_review']}{c.RESET}  {c.DIM}[NEEDS_REVIEW]{c.RESET}")
        lines.append(f"  {c.KEY}Clés supprimées  {c.RESET}: {c.RED}{data['removed']}{c.RESET}")
        lines.append(f"  {c.KEY}Total            {c.RESET}: {c.WHITE}{data['total']}{c.RESET}")

        if data['added_keys']:
            lines.append(f"  {c.DIM}Nouvelles clés:{c.RESET}")
            for key in data['added_keys'][:5]:
                lines.append(f"    {c.GREEN}+{c.RESET} {c.DIM}{key}{c.RESET}")
            if len(data['added_keys']) > 5:
                lines.append(f"    {c.DIM}... et {len(data['added_keys']) - 5} autres{c.RESET}")

        if data['review_keys']:
            lines.append(f"  {c.DIM}Clés à réviser:{c.RESET}")
            for key in data['review_keys'][:5]:
                lines.append(f"    {c.YELLOW}?{c.RESET} {c.DIM}{key}{c.RESET}")
            if len(data['review_keys']) > 5:
                lines.append(f"    {c.DIM}... et {len(data['review_keys']) - 5} autres{c.RESET}")

        lines.append("")

    lines.append(f"{c.separator()}")
    lines.append(f"{c.TITLE}TOTAL{c.RESET}")
    lines.append(f"{c.separator()}")
    lines.append(f"  {c.KEY}Langues traitées {c.RESET}: {c.WHITE}{len(results)}{c.RESET}")
    lines.append(f"  {c.KEY}Clés ajoutées    {c.RESET}: {c.GREEN}{total_added}{c.RESET}")
    lines.append(f"  {c.KEY}Clés à réviser   {c.RESET}: {c.YELLOW}{total_review}{c.RESET}")
    lines.append(f"  {c.KEY}Clés supprimées  {c.RESET}: {c.RED}{total_removed}{c.RESET}")

    return "\n".join(lines)


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_sync():
    """Menu interactif pour SYNC."""
    from TM_common import clear_screen, print_header

    clear_screen()
    print_header()
    print(f"\n{c.INFO}SYNC{c.RESET}: Synchroniser les langues étrangères")
    print(c.separator())

    print(f"\n{c.KEY}Avez-vous un dossier UPDATE{c.RESET} (généré par COMPARE) ?")
    print(f"{c.DIM}  (Permet de marquer les clés [NEEDS_REVIEW]){c.RESET}")
    has_update = input(f"{c.PROMPT}  [O/n]: {c.RESET}").strip().lower()

    update_dir = None
    ref_path = None
    locales_dir = None

    if has_update in ['o', 'y', '', 'oui', 'yes']:
        print(f"\n{c.KEY}Dossier UPDATE{c.RESET} (contenant UPDATE_en.json):")
        update_dir = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not update_dir or not os.path.isdir(update_dir):
            print(c.error("Répertoire invalide."))
            input("\nAppuyez sur Entrée...")
            return None
    else:
        print(f"\n{c.KEY}Fichier EN de référence{c.RESET} (ou répertoire):")
        ref_path = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not ref_path:
            print(c.error("Chemin requis."))
            input("\nAppuyez sur Entrée...")
            return None

    print(f"\n{c.KEY}Répertoire des fichiers de langues{c.RESET} (Locales):")
    print(f"{c.DIM}  (Entrée = même répertoire que la référence){c.RESET}")
    locales_dir = input(f"{c.PROMPT}  > {c.RESET}").strip() or None

    try:
        print(f"\n{c.INFO}[INFO]{c.RESET} Synchronisation en cours...")
        results = run_sync(ref_path, locales_dir, update_dir)

        if not results:
            print(c.warning("Aucune langue étrangère trouvée."))
        else:
            print()
            print(generate_sync_report(results))
            print()
            print(c.success("Fichiers mis à jour (backups .bak créés)"))
            print()
            print(f"{c.INFO}[INFO]{c.RESET} PROCHAINE ÉTAPE:")
            print(f"{c.DIM}  Recherchez [NEW] et [NEEDS_REVIEW] dans les fichiers{c.RESET}")
            print(f"{c.DIM}  pour compléter les traductions.{c.RESET}")

        return results

    except FileNotFoundError as e:
        print(c.error(f"Fichier non trouvé: {e}"))
    except Exception as e:
        print(c.error(f"Erreur: {e}"))

    input("\nAppuyez sur Entrée pour continuer...")
    return None
