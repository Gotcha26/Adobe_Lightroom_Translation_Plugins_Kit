#!/usr/bin/env python3
"""
Nom du fichier : sync.py

Dépendances : common

Description :
Module SYNC pour Translator.
Synchronise les langues étrangères avec le fichier EN de référence.

Fonctionne en deux modes :
  - Mode sans UPDATE: Fusion simple des fichiers de langue avec fichier de référence
  - Mode avec UPDATE: Utilise UPDATE_{lang}.json pour marquer les changements

Permet de garder les fichiers de langue synchronisés avec la version anglaise
de référence lorsqu'il y a des modifications du code.

Usage CLI :
Non fourni

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import shutil
from datetime import datetime
from typing import Dict, List, Set, Optional

from .common import (
    parse_translation_file, write_translation_file, update_translation_file_surgical,
    resolve_path, load_update_json, find_languages, c
)
from .config_loader import get_reference_filename


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_sync(reference_path: Optional[str] = None, locales_dir: Optional[str] = None,
             update_dir: Optional[str] = None, backup_dir: Optional[str] = None) -> Dict[str, Dict]:
    """
    Synchronise les langues étrangères avec le fichier de référence.

    Modes:
        1. Avec --update: utilise UPDATE_{lang}.json pour marquer les changements
        2. Sans --update: synchronisation simple des clés

    Args:
        reference_path: Fichier de référence (ou répertoire)
        locales_dir: Répertoire des fichiers de langues
        update_dir: Répertoire contenant UPDATE_{lang}.json (optionnel)
        backup_dir: Répertoire pour les backups (si None, crée .bak à côté du fichier)

    Returns:
        Dict par langue avec les statistiques
    """
    # Charger les données de mise à jour si disponibles
    update_data = None
    if update_dir:
        update_data = load_update_json(update_dir)
        # Utiliser le fichier de référence du dossier update
        ref_filename = get_reference_filename()
        ref_in_update = os.path.join(update_dir, ref_filename)
        if os.path.isfile(ref_in_update):
            reference_path = ref_in_update

    # Résoudre le chemin de référence
    if not reference_path:
        raise ValueError(_("Chemin de référence requis (--ref ou via --update)"))

    ref_dir, ref_file = resolve_path(reference_path)

    # Déterminer le répertoire des locales
    if not locales_dir:
        locales_dir = ref_dir

    # Charger le fichier de référence
    ref_strings = parse_translation_file(ref_file)
    ref_keys = set(ref_strings.keys())

    # Trouver les langues étrangères
    other_languages = find_languages(locales_dir, exclude_reference=True)

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
            lang, lang_file, ref_strings, ref_keys,
            added_keys, changed_keys, deleted_keys,
            locales_dir, update_data, backup_dir
        )
        results[lang] = result

    return results


def _sync_language(lang: str, lang_file: str, ref_strings: Dict[str, str],
                   ref_keys: Set[str], added_keys: Set[str], changed_keys: Set[str],
                   deleted_keys: Set[str], output_dir: str,
                   update_data: Optional[Dict] = None, backup_dir: Optional[str] = None) -> Dict:
    """Synchronise une langue avec le fichier de référence."""

    # Charger la langue actuelle
    if os.path.isfile(lang_file):
        lang_strings = parse_translation_file(lang_file)
        # Créer backup
        if backup_dir:
            os.makedirs(backup_dir, exist_ok=True)
            backup_filename = os.path.basename(lang_file) + '.bak'
            backup_path = os.path.join(backup_dir, backup_filename)
            shutil.copy2(lang_file, backup_path)
        else:
            shutil.copy2(lang_file, lang_file + '.bak')
    else:
        lang_strings = {}

    lang_keys = set(lang_strings.keys())

    # Calculer les différences
    missing_in_lang = ref_keys - lang_keys
    extra_in_lang = lang_keys - ref_keys
    common_keys = ref_keys & lang_keys

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

        # Marquer si le texte de référence a changé (UNIQUEMENT si update_data fourni via COMPARE)
        if update_data and key in changed_keys:
            markers[key] = _("-- [NEEDS_REVIEW] Reference text was modified")
            stats['needs_review'] += 1

    # Clés manquantes : ajouter avec valeur de référence
    for key in missing_in_lang:
        new_strings[key] = ref_strings[key]  # Valeur de référence par défaut
        # Marquer UNIQUEMENT si update_data fourni via COMPARE
        if update_data:
            markers[key] = _("-- [NEW] To translate")
        stats['added'] += 1

    # Clés en trop : ne pas copier (= supprimées)
    stats['removed'] = len(extra_in_lang)

    # Métadonnées pour l'entête
    metadata = {
        'new_keys': stats['added'],
        'changed_keys': stats['needs_review'],
        'source': 'SYNC',
        'total_keys': len(new_strings)
    }

    # Écrire le fichier avec mise à jour chirurgicale
    output_file = os.path.join(output_dir, f'TranslatedStrings_{lang}.txt')
    update_translation_file_surgical(output_file, update_data, new_strings, markers, metadata)

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
    lines.append(_("{var0}RAPPORT DE SYNCHRONISATION{var1}").format(var0=c.TITLE, var1=c.RESET))
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
        lines.append(_("  {var0}Clés conservées  {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.WHITE, var3=data['kept'], var4=c.RESET))
        lines.append(_("  {var0}Clés ajoutées    {var1}: {var2}{var3}{var4}  {var5}[NEW] à traduire{var6}").format(var0=c.KEY, var1=c.RESET, var2=c.GREEN, var3=data['added'], var4=c.RESET, var5=c.DIM, var6=c.RESET))
        lines.append(_("  {var0}Clés à réviser   {var1}: {var2}{var3}{var4}  {var5}[NEEDS_REVIEW]{var6}").format(var0=c.KEY, var1=c.RESET, var2=c.YELLOW, var3=data['needs_review'], var4=c.RESET, var5=c.DIM, var6=c.RESET))
        lines.append(_("  {var0}Clés supprimées  {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.RED, var3=data['removed'], var4=c.RESET))
        lines.append(_("  {var0}Total            {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.WHITE, var3=data['total'], var4=c.RESET))

        if data['added_keys']:
            lines.append(_("  {var0}Nouvelles clés:{var1}").format(var0=c.DIM, var1=c.RESET))
            for key in data['added_keys'][:5]:
                lines.append(f"    {c.GREEN}+{c.RESET} {c.DIM}{key}{c.RESET}")
            if len(data['added_keys']) > 5:
                lines.append(_("    {var0}... et {var1} autres{var2}").format(var0=c.DIM, var1=len(data['added_keys']) - 5, var2=c.RESET))

        if data['review_keys']:
            lines.append(_("  {var0}Clés à réviser:{var1}").format(var0=c.DIM, var1=c.RESET))
            for key in data['review_keys'][:5]:
                lines.append(f"    {c.YELLOW}?{c.RESET} {c.DIM}{key}{c.RESET}")
            if len(data['review_keys']) > 5:
                lines.append(_("    {var0}... et {var1} autres{var2}").format(var0=c.DIM, var1=len(data['review_keys']) - 5, var2=c.RESET))

        lines.append("")

    lines.append(f"{c.separator()}")
    lines.append(_("{var0}TOTAL{var1}").format(var0=c.TITLE, var1=c.RESET))
    lines.append(f"{c.separator()}")
    lines.append(_("  {var0}Langues traitées {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.WHITE, var3=len(results), var4=c.RESET))
    lines.append(_("  {var0}Clés ajoutées    {var1}: {var2}{total_added}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.GREEN, total_added=total_added, var4=c.RESET))
    lines.append(_("  {var0}Clés à réviser   {var1}: {var2}{total_review}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.YELLOW, total_review=total_review, var4=c.RESET))
    lines.append(_("  {var0}Clés supprimées  {var1}: {var2}{total_removed}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.RED, total_removed=total_removed, var4=c.RESET))

    return "\n".join(lines)


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_sync(plugin_path: str = ""):
    """Menu interactif pour SYNC.

    Args:
        plugin_path: Chemin du plugin (optionnel) pour auto-détection
    """
    from .common import clear_screen, print_header
    from core.paths import find_latest_tool_output
    from core.menu_helpers import select_tool_output_dir

    clear_screen()
    print_header()
    print(_("\n{var0}SYNC{var1}: Synchroniser les langues étrangères").format(var0=c.INFO, var1=c.RESET))
    print(c.separator())

    print(_("\n{var0}Avez-vous un dossier UPDATE{var1} (généré par COMPARE) ?").format(var0=c.KEY, var1=c.RESET))
    print(_("{var0}  (Permet de marquer les clés [NEEDS_REVIEW]){var1}").format(var0=c.DIM, var1=c.RESET))
    has_update = input(_("{var0}  [O/n]: {var1}").format(var0=c.PROMPT, var1=c.RESET)).strip().lower()

    update_dir = None
    ref_path = None
    locales_dir = None

    if has_update in ['o', 'y', '', 'oui', 'yes']:
        # Auto-détection et sélection interactive si plugin_path fourni
        if plugin_path:
            update_dir = select_tool_output_dir(plugin_path, "Translator", "")
            if update_dir:
                print(_("\n{var0}[INFO]{var1} Dossier sélectionné: {var2}{update_dir}{var4}").format(var0=c.INFO, var1=c.RESET, var2=c.VALUE, update_dir=update_dir, var4=c.RESET))
            else:
                print(c.warning(_("Aucun dossier Translator sélectionné")))

        if not update_dir:
            update_filename = get_update_filename()
            print(_("\n{var0}Dossier UPDATE{var1} (contenant {update_filename}):").format(var0=c.KEY, var1=c.RESET, update_filename=update_filename))
            update_dir = input(f"{c.PROMPT}  > {c.RESET}").strip()
            if not update_dir or not os.path.isdir(update_dir):
                print(c.error(_("Répertoire invalide.")))
                input(_("\nAppuyez sur Entrée..."))
                return None
    else:
        print(_("\n{var0}Fichier EN de référence{var1} (ou répertoire):").format(var0=c.KEY, var1=c.RESET))
        ref_path = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not ref_path:
            print(c.error(_("Chemin requis.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

    print(_("\n{var0}Répertoire des fichiers de langues{var1} (Locales):").format(var0=c.KEY, var1=c.RESET))
    print(_("{var0}  (Entrée = même répertoire que la référence){var1}").format(var0=c.DIM, var1=c.RESET))
    locales_dir = input(f"{c.PROMPT}  > {c.RESET}").strip() or None

    try:
        print(_("\n{var0}[INFO]{var1} Synchronisation en cours...").format(var0=c.INFO, var1=c.RESET))
        results = run_sync(ref_path, locales_dir, update_dir)

        if not results:
            print(c.warning(_("Aucune langue étrangère trouvée.")))
        else:
            print()
            print(generate_sync_report(results))
            print()
            print(c.success(_("Fichiers mis à jour (backups .bak créés)")))
            print()
            print(_("{var0}[INFO]{var1} PROCHAINE ÉTAPE:").format(var0=c.INFO, var1=c.RESET))
            print(_("{var0}  Recherchez [NEW] et [NEEDS_REVIEW] dans les fichiers{var1}").format(var0=c.DIM, var1=c.RESET))
            print(_("{var0}  pour compléter les traductions.{var1}").format(var0=c.DIM, var1=c.RESET))

        return results

    except FileNotFoundError as e:
        print(c.error(_("Fichier non trouvé: {e}").format(e=e)))
    except Exception as e:
        print(c.error(_("Erreur: {e}").format(e=e)))

    input(_("\nAppuyez sur Entrée pour continuer..."))
    return None
