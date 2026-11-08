#!/usr/bin/env python3
"""
Nom du fichier : inject.py

Dépendances : common

Description :
Module INJECT pour Translator.
Réinjecte les traductions depuis TRANSLATE_xx.txt dans les fichiers de langue.

Important :
  - Les clés non traduites (valeur vide) reçoivent la valeur EN par défaut
  - Fusionne les traductions complétées avec les fichiers de langue existants
  - Gère les metadonnées de traduction et les changements

Usage CLI :
Non fourni

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import shutil
from typing import Dict, Optional

from .common import (
    parse_translation_file, update_translation_file_surgical,
    load_update_json, c, escape_translation_value,
    TRANSLATE_KEY, TRANSLATE_ARROW, translate_ref_marker, translate_after_marker,
)
from .config_loader import get_reference_lang
from core.i18n import _
from core.paths import backup_once, local_backup_path, get_translator_backup_dir


def _marker_value(line, markers):
    """Valeur après le premier marqueur de `markers` qui ouvre la ligne, sinon None."""
    for m in markers:
        if line.startswith(m):
            rest = line[len(m):]
            if rest.lstrip().startswith(TRANSLATE_ARROW):
                return None  # ligne de traduction cible, pas une valeur de référence
            return rest.strip()
    return None


# =============================================================================
# PARSER TRANSLATE
# =============================================================================

def parse_translate_file(file_path: str, update_data: Optional[Dict] = None) -> Dict[str, str]:
    """
    Parse un fichier TRANSLATE_xx.txt et extrait les traductions.

    IMPORTANT:
    - Si une traduction est fournie après → : on l'utilise
    - Si → est vide : on utilise la valeur EN depuis update_data

    Args:
        file_path: Chemin du fichier TRANSLATE_xx.txt
        update_data: Données UPDATE_{lang}.json pour récupérer les valeurs EN

    Returns:
        Dict[str, str]: {clé: traduction}
    """
    translations = {}
    current_key = None
    current_en_value = None

    ref_lang = get_reference_lang()
    # Rétrocompatibilité : anciens fichiers écrits avec [EN] / [EN APRÈS] (marqueurs
    # codés en dur, passés par _() donc parfois traduits en [EN AFTER]) avant #21.
    ref_markers = (translate_ref_marker(ref_lang), "[EN]")
    after_markers = (translate_after_marker(ref_lang), "[EN APRÈS]", "[EN AFTER]")

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
            if line.startswith(TRANSLATE_KEY):
                current_key = line[len(TRANSLATE_KEY):].strip()
                current_en_value = en_values.get(current_key, '')

            # Détecter [<REF> AFTER] pour les clés modifiées
            elif _marker_value(line, after_markers) is not None:
                if current_key:
                    current_en_value = _marker_value(line, after_markers)

            # Détecter la valeur de référence (pour les clés non dans update_data)
            elif _marker_value(line, ref_markers) is not None:
                if current_key and not current_en_value:
                    current_en_value = _marker_value(line, ref_markers)

            # Détecter la traduction (ligne avec →)
            elif '] → ' in line or '] →' in line:
                parts = line.split('→', 1)
                if len(parts) == 2 and current_key:
                    translation = parts[1].strip()

                    if translation:
                        # Traduction fournie : « " » brut échappé, sinon la ligne
                        # écrite ne serait plus relisible (KEY_LINE_RE)
                        translations[current_key] = escape_translation_value(translation)
                    else:
                        # Pas de traduction → utiliser valeur EN
                        translations[current_key] = current_en_value or ''

    return translations


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_inject(translate_file: str, target_file: str,
               update_dir: Optional[str] = None, create_backup: bool = True,
               backup_dir: Optional[str] = None) -> Dict:
    """
    Injecte les traductions d'un fichier TRANSLATE dans un fichier de langue.

    Args:
        translate_file: Fichier TRANSLATE_xx.txt avec les traductions
        target_file: Fichier TranslatedStrings_xx.txt cible
        update_dir: Répertoire contenant UPDATE_{lang}.json (pour valeurs EN par défaut)
        create_backup: Créer une sauvegarde .bak
        backup_dir: Répertoire pour les backups (si None, sous-dossier backups/ à côté du fichier)

    Returns:
        Statistiques d'injection
    """
    # Charger UPDATE_{lang}.json si disponible
    update_data = None
    if update_dir:
        update_data = load_update_json(update_dir)
    else:
        # Essayer de trouver UPDATE_{lang}.json dans le même dossier que TRANSLATE
        translate_dir = os.path.dirname(translate_file)
        update_data = load_update_json(translate_dir)

    # Parser le fichier de traduction
    new_translations = parse_translate_file(translate_file, update_data)

    if not new_translations:
        return {'injected': 0, 'from_ref': 0, 'skipped': 0, 'total': 0}

    # Charger le fichier cible existant
    if os.path.isfile(target_file):
        existing = parse_translation_file(target_file)
        if create_backup:
            if backup_dir:
                # Backup de session : ne jamais écraser l'original déjà sauvegardé
                backup_once(target_file, os.path.dirname(target_file), backup_dir)
            else:
                # Par défaut : sous-dossier backups/ à côté du fichier cible
                backup_path = local_backup_path(target_file)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(target_file, backup_path)
    else:
        existing = {}

    # Fusionner
    stats = {'injected': 0, 'from_ref': 0, 'skipped': 0}

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
                stats['from_ref'] += 1
            else:
                stats['injected'] += 1
            existing[key] = translation
        else:
            stats['skipped'] += 1

    stats['total'] = len(existing)

    # Métadonnées pour l'entête
    metadata = {
        'new_keys': stats['injected'] + stats['from_ref'],
        'source': os.path.basename(translate_file)
    }

    # Écrire le fichier avec mise à jour chirurgicale
    update_translation_file_surgical(target_file, update_data, existing, metadata=metadata)

    return stats


def run_inject_from_dir(translate_dir: str, locales_dir: str,
                        update_dir: Optional[str] = None,
                        create_backup: bool = True,
                        backup_dir: Optional[str] = None) -> Dict[str, Dict]:
    """
    Injecte tous les fichiers TRANSLATE_*.txt dans les fichiers de langue.

    Args:
        translate_dir: Répertoire contenant les fichiers TRANSLATE_*.txt
        locales_dir: Répertoire des fichiers TranslatedStrings_*.txt
        update_dir: Répertoire UPDATE (défaut: translate_dir)
        create_backup: Créer des sauvegardes .bak
        backup_dir: Répertoire des sauvegardes (défaut: backups/ à côté de chaque fichier cible)

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
                stats = run_inject(translate_file, target_file, update_dir, create_backup, backup_dir)
                results[lang] = stats
            except Exception as e:
                results[lang] = {'error': str(e)}

    return results


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_inject(plugin_path: str = ""):
    """Menu interactif pour INJECT.

    Args:
        plugin_path: Chemin du plugin (optionnel) pour auto-détection
    """
    from .common import clear_screen, print_header

    clear_screen()
    print_header()
    print(_("\n{var0}INJECT{var1}: Réinjecter les traductions").format(var0=c.INFO, var1=c.RESET))
    print(c.separator())
    print(_("\n{var0}[ATTENTION]{var1} Les clés non traduites (→ vide) recevront la valeur EN").format(var0=c.WARNING, var1=c.RESET))

    print(_("\n{var0}Mode{var1}:").format(var0=c.KEY, var1=c.RESET))
    print(_("  {var0}1{var1}. Injecter un fichier TRANSLATE_xx.txt spécifique").format(var0=c.YELLOW, var1=c.RESET))
    print(_("  {var0}2{var1}. Injecter tous les fichiers TRANSLATE_*.txt d'un dossier").format(var0=c.YELLOW, var1=c.RESET))
    mode = input(_("\n{var0}  Choix (1-2): {var1}").format(var0=c.PROMPT, var1=c.RESET)).strip()

    if mode == '1':
        print(_("\n{var0}Fichier TRANSLATE_xx.txt{var1}:").format(var0=c.KEY, var1=c.RESET))
        translate_file = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not translate_file or not os.path.isfile(translate_file):
            print(c.error(_("Fichier invalide.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

        print(_("\n{var0}Fichier cible TranslatedStrings_xx.txt{var1}:").format(var0=c.KEY, var1=c.RESET))
        target_file = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not target_file:
            print(c.error(_("Chemin requis.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

        print(_("\n{var0}Dossier UPDATE{var1} (contenant UPDATE_xx.json):").format(var0=c.KEY, var1=c.RESET))
        print(_("{var0}  (Entrée = même dossier que TRANSLATE){var1}").format(var0=c.DIM, var1=c.RESET))
        update_dir = input(f"{c.PROMPT}  > {c.RESET}").strip() or None

        try:
            print(_("\n{var0}[INFO]{var1} Injection en cours...").format(var0=c.INFO, var1=c.RESET))
            stats = run_inject(translate_file, target_file, update_dir,
                               backup_dir=get_translator_backup_dir(plugin_path))

            print(f"\n{c.HEADER}{'=' * 66}{c.RESET}")
            print(_("{var0}  RÉSULTAT{var1}").format(var0=c.TITLE, var1=c.RESET))
            print(f"{c.HEADER}{'=' * 66}{c.RESET}")
            print(_("  {var0}Traductions injectées  {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.GREEN, var3=stats['injected'], var4=c.RESET))
            print(_("  {var0}Valeurs EN par défaut  {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.CYAN, var3=stats['from_ref'], var4=c.RESET))
            print(_("  {var0}Entrées ignorées       {var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.DIM, var3=stats['skipped'], var4=c.RESET))
            print(_("  {var0}Total clés dans fichier{var1}: {var2}{var3}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.WHITE, var3=stats['total'], var4=c.RESET))
            print()
            print(c.success(_("Fichier mis à jour: {var0}{target_file}{var2}").format(var0=c.VALUE, target_file=target_file, var2=c.RESET)))
            print(_("{var0}  (Backup .bak créé dans backups/){var1}").format(var0=c.DIM, var1=c.RESET))

            return stats

        except Exception as e:
            print(c.error(_("Erreur: {e}").format(e=e)))

    elif mode == '2':
        print(_("\n{var0}Dossier contenant les fichiers TRANSLATE_*.txt{var1}:").format(var0=c.KEY, var1=c.RESET))
        translate_dir = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not translate_dir or not os.path.isdir(translate_dir):
            print(c.error(_("Répertoire invalide.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

        print(_("\n{var0}Répertoire des fichiers de langue{var1} (Locales):").format(var0=c.KEY, var1=c.RESET))
        locales_dir = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not locales_dir or not os.path.isdir(locales_dir):
            print(c.error(_("Répertoire invalide.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

        print(_("\n{var0}Dossier UPDATE{var1} (contenant UPDATE_xx.json):").format(var0=c.KEY, var1=c.RESET))
        print(_("{var0}  (Entrée = même dossier que TRANSLATE){var1}").format(var0=c.DIM, var1=c.RESET))
        update_dir = input(f"{c.PROMPT}  > {c.RESET}").strip() or None

        try:
            print(_("\n{var0}[INFO]{var1} Injection en cours...").format(var0=c.INFO, var1=c.RESET))
            results = run_inject_from_dir(translate_dir, locales_dir, update_dir,
                                          backup_dir=get_translator_backup_dir(plugin_path))

            if results:
                print(f"\n{c.HEADER}{'=' * 66}{c.RESET}")
                print(_("{var0}  RÉSULTAT{var1}").format(var0=c.TITLE, var1=c.RESET))
                print(f"{c.HEADER}{'=' * 66}{c.RESET}")
                for lang, stats in sorted(results.items()):
                    if 'error' in stats:
                        print(_("  {var0}[{var1}]{var2} {var3}[ERREUR]{var4} {var5}").format(var0=c.RED, var1=lang.upper(), var2=c.RESET, var3=c.ERROR, var4=c.RESET, var5=stats['error']))
                    else:
                        translated = stats['injected']
                        from_ref = stats['from_ref']
                        print(_("  {var0}[{var1}]{var2} {var3}[OK]{var4} {var5}{translated}{var7} traduites + {var8}{from_ref}{var10} EN par défaut").format(var0=c.CYAN, var1=lang.upper(), var2=c.RESET, var3=c.OK, var4=c.RESET, var5=c.GREEN, translated=translated, var7=c.RESET, var8=c.CYAN, from_ref=from_ref, var10=c.RESET))
                print()
                print(c.success(_("Fichiers mis à jour (backups .bak créés)")))

                return results
            else:
                print(c.warning(_("Aucun fichier TRANSLATE_*.txt trouvé")))

        except Exception as e:
            print(c.error(_("Erreur: {e}").format(e=e)))

    else:
        print(c.error(_("Choix invalide.")))
        input(_("\nAppuyez sur Entrée..."))
        return None

    input(_("\nAppuyez sur Entrée pour continuer..."))
    return None
