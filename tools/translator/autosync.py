#!/usr/bin/env python3
"""
Nom du fichier : TM_autosync.py

Dépendances : TM_sync, common.paths, common.colors

Description :
Synchronisation automatique intelligente des fichiers de traduction.

Cette commande détecte automatiquement la dernière extraction et synchronise
tous les fichiers TranslatedStrings_xx.txt existants dans le plugin.

C'est le raccourci idéal pour la maintenance courante :
  - Détecte la dernière extraction
  - Trouve automatiquement tous les fichiers de langue existants
  - Synchronise tout d'un coup
  - Génère un rapport détaillé

Usage CLI :
    python TM_autosync.py                    # Menu interactif
    python TM_autosync.py /path/to/plugin    # Chemin direct du plugin

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.paths import find_latest_tool_output, get_tool_output_path
from core.colors import Colors
from .sync import run_sync

c = Colors()


def find_all_translation_files(plugin_path: str) -> list[str]:
    """
    Trouve tous les fichiers TranslatedStrings_xx.txt dans le plugin.

    Args:
        plugin_path: Chemin du plugin

    Returns:
        Liste des chemins complets des fichiers trouvés
    """
    translation_files = []

    if not os.path.isdir(plugin_path):
        return []

    for filename in os.listdir(plugin_path):
        if filename.startswith("TranslatedStrings_") and filename.endswith(".txt"):
            full_path = os.path.join(plugin_path, filename)
            translation_files.append(full_path)

    return translation_files


def menu_autosync(plugin_path: str):
    """Menu interactif pour Auto-Sync."""
    from .common import clear_screen, print_header

    clear_screen()
    print_header()

    print(f"\n{c.TITLE}  AUTO-SYNC - Synchronisation automatique{c.RESET}")
    print(c.separator())

    # Vérifier le plugin
    if not plugin_path or not os.path.isdir(plugin_path):
        print(c.error("Plugin non configuré ou introuvable."))
        return

    # Trouver les fichiers de traduction existants
    translation_files = find_all_translation_files(plugin_path)

    if not translation_files:
        print(c.warning("Aucun fichier TranslatedStrings_xx.txt trouvé dans le plugin."))
        print()
        print(f"{c.INFO}Première installation ?{c.RESET}")
        print("  → Utilisez la commande INSTALL pour installer les fichiers depuis l'extraction")
        return

    print(f"\n{c.INFO}[INFO]{c.RESET} Fichiers de traduction détectés:")
    for f in translation_files:
        filename = os.path.basename(f)
        print(f"  - {c.VALUE}{filename}{c.RESET}")
    print()

    # Trouver la dernière extraction
    latest_extraction = find_latest_tool_output(plugin_path, "Extractor")

    if not latest_extraction:
        print(c.error("Aucune extraction trouvée."))
        print()
        print("Lancez d'abord l'Extractor pour générer un nouveau TranslatedStrings_en.txt")
        return

    # Chercher le TranslatedStrings_en.txt dans l'extraction
    ref_en_path = os.path.join(latest_extraction, "TranslatedStrings_en.txt")

    if not os.path.isfile(ref_en_path):
        print(c.error(f"TranslatedStrings_en.txt introuvable dans l'extraction"))
        print(f"  Recherché: {ref_en_path}")
        return

    print(f"{c.INFO}[INFO]{c.RESET} Dernière extraction:")
    print(f"  {c.VALUE}{os.path.basename(latest_extraction)}{c.RESET}")
    print(f"  Référence: {c.VALUE}TranslatedStrings_en.txt{c.RESET}")
    print()

    print(f"{c.INFO}Synchronisation automatique:{c.RESET}")
    print(f"  - Ajoute les nouvelles clés {c.YELLOW}(en anglais){c.RESET}")
    print(f"  - Replace les clés modifiées {c.YELLOW}(en anglais){c.RESET}")
    print("  - Supprime les clés obsolètes")
    print("  - Préserve les traductions existantes")
    print()

    # Demander confirmation
    choice = input(f"{c.PROMPT}Lancer la synchronisation? (O/n): {c.RESET}").strip().lower()

    if choice in ['n', 'non', 'no']:
        print(c.warning("Synchronisation annulée"))
        return

    # Créer le dossier de sortie
    output_dir = get_tool_output_path(plugin_path, "Translator", create=True)

    # Exécuter SYNC pour chaque fichier de langue
    print()
    print(c.separator())
    print(f"{c.TITLE}Synchronisation en cours...{c.RESET}")
    print(c.separator())

    synced_files = []
    errors = []

    for lang_file in translation_files:
        filename = os.path.basename(lang_file)

        # Extraire le code langue (ex: "fr" de "TranslatedStrings_fr.txt")
        if filename == "TranslatedStrings_en.txt":
            continue  # Skip EN (c'est la référence)

        lang_code = filename.replace("TranslatedStrings_", "").replace(".txt", "")

        print()
        print(f"{c.INFO}► Langue: {c.VALUE}{lang_code}{c.RESET}")

        try:
            # Créer un répertoire temporaire pour synchroniser ce fichier
            temp_sync_dir = os.path.join(output_dir, f"temp_{lang_code}")
            os.makedirs(temp_sync_dir, exist_ok=True)

            # Copier le fichier de langue dans le répertoire temporaire
            shutil.copy2(lang_file, os.path.join(temp_sync_dir, filename))

            # Exécuter SYNC avec les bons paramètres
            results = run_sync(
                reference_path=ref_en_path,
                locales_dir=temp_sync_dir
            )

            if results and lang_code in results:
                # Copier le fichier synchronisé vers la sortie
                synced_file = os.path.join(temp_sync_dir, filename)
                output_file = os.path.join(output_dir, filename)
                if os.path.exists(synced_file):
                    shutil.copy2(synced_file, output_file)
                    synced_files.append((lang_code, output_file))

                    # Générer un mini-rapport
                    report = results.get(lang_code, {})
                    if report:
                        print(f"  {c.SUCCESS}✓{c.RESET} {report.get('added', 0)} ajoutées, "
                              f"{report.get('modified', 0)} modifiées, "
                              f"{report.get('deleted', 0)} supprimées")
            else:
                errors.append(filename)
                print(c.error(f"  Échec de la synchronisation"))

            # Nettoyer le répertoire temporaire
            shutil.rmtree(temp_sync_dir, ignore_errors=True)

        except Exception as e:
            errors.append(filename)
            print(c.error(f"  Erreur: {e}"))

    # Résumé final
    print()
    print(c.separator())

    if errors:
        print(c.warning(f"\n⚠ {len(errors)} fichier(s) en erreur:"))
        for err in errors:
            print(f"  - {err}")

    if synced_files:
        print(c.success(f"\n✓ {len(synced_files)} fichier(s) synchronisé(s):"))
        for lang, filepath in synced_files:
            print(f"  {c.VALUE}{lang}{c.RESET}: {c.DIM}{filepath}{c.RESET}")

        print()
        print(f"{c.INFO}Prochaines étapes:{c.RESET}")
        print(f"  1. Copiez les fichiers synchronisés dans le plugin:")
        print(f"     {c.DIM}cp {output_dir}/TranslatedStrings_*.txt {plugin_path}/{c.RESET}")
        print()
        print(f"  2. Recherchez les {c.YELLOW}clés en anglais{c.RESET} (nouvelles ou modifiées)")
        print("  3. Traduisez les clés concernées")
        print("  4. Commitez les changements (si GitHub workflow)")


def run_autosync(plugin_path: str) -> bool:
    """
    Exécute Auto-Sync en mode CLI.

    Args:
        plugin_path: Chemin du plugin

    Returns:
        bool: Succès
    """
    if not plugin_path or not os.path.isdir(plugin_path):
        print(c.error("Chemin du plugin invalide"))
        return False

    # Trouver les fichiers de traduction
    translation_files = find_all_translation_files(plugin_path)

    if not translation_files:
        print(c.error("Aucun fichier TranslatedStrings_xx.txt trouvé"))
        return False

    # Trouver la dernière extraction
    latest_extraction = find_latest_tool_output(plugin_path, "Extractor")

    if not latest_extraction:
        print(c.error("Aucune extraction trouvée"))
        return False

    ref_en_path = os.path.join(latest_extraction, "TranslatedStrings_en.txt")

    if not os.path.isfile(ref_en_path):
        print(c.error("TranslatedStrings_en.txt introuvable dans l'extraction"))
        return False

    # Créer le dossier de sortie
    output_dir = get_tool_output_path(plugin_path, "Translator", create=True)

    # Synchroniser tous les fichiers
    synced = 0
    for lang_file in translation_files:
        filename = os.path.basename(lang_file)
        if filename == "TranslatedStrings_en.txt":
            continue

        try:
            # Créer un répertoire temporaire pour synchroniser ce fichier
            lang_code = filename.replace("TranslatedStrings_", "").replace(".txt", "")
            temp_sync_dir = os.path.join(output_dir, f"temp_{lang_code}")
            os.makedirs(temp_sync_dir, exist_ok=True)

            # Copier le fichier de langue dans le répertoire temporaire
            shutil.copy2(lang_file, os.path.join(temp_sync_dir, filename))

            # Exécuter SYNC avec les bons paramètres
            results = run_sync(
                reference_path=ref_en_path,
                locales_dir=temp_sync_dir
            )

            if results and lang_code in results:
                synced += 1
                print(c.success(f"✓ {filename}"))
                # Copier le fichier synchronisé vers la sortie
                synced_file = os.path.join(temp_sync_dir, filename)
                output_file = os.path.join(output_dir, filename)
                if os.path.exists(synced_file):
                    shutil.copy2(synced_file, output_file)

            # Nettoyer le répertoire temporaire
            shutil.rmtree(temp_sync_dir, ignore_errors=True)

        except Exception as e:
            print(c.error(f"✗ {filename}: {e}"))

    if synced > 0:
        print()
        print(c.success(f"✓ {synced} fichier(s) synchronisé(s) dans {output_dir}"))
        return True
    else:
        return False
