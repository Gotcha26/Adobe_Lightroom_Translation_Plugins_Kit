#!/usr/bin/env python3
"""
TM_autosync.py

Synchronisation automatique intelligente des fichiers de traduction.

Cette commande détecte automatiquement la dernière extraction et synchronise
tous les fichiers TranslatedStrings_xx.txt existants dans le plugin.

C'est le raccourci idéal pour la maintenance courante :
  - Détecte la dernière extraction
  - Trouve automatiquement tous les fichiers de langue existants
  - Synchronise tout d'un coup
  - Génère un rapport

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-01-31
Version: 1.0
"""

import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import find_latest_tool_output
from common.colors import Colors
from TM_sync import run_sync, generate_sync_report

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
    from TM_common import clear_screen, print_header, get_tool_output_path

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
    output_dir, timestamp = get_tool_output_path(plugin_path, "3_Translator")

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
            # Exécuter SYNC
            updated_file = run_sync(
                ref_en_path=ref_en_path,
                lang_file_path=lang_file,
                output_dir=output_dir
            )

            if updated_file and os.path.exists(updated_file):
                synced_files.append((lang_code, updated_file))

                # Générer un mini-rapport
                report = generate_sync_report(ref_en_path, lang_file, updated_file)
                if report:
                    print(f"  {c.SUCCESS}✓{c.RESET} {report.get('added', 0)} ajoutées, "
                          f"{report.get('modified', 0)} modifiées, "
                          f"{report.get('deleted', 0)} supprimées")
            else:
                errors.append(filename)
                print(c.error(f"  Échec de la synchronisation"))

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
    from TM_common import get_tool_output_path
    output_dir, timestamp = get_tool_output_path(plugin_path, "3_Translator")

    # Synchroniser tous les fichiers
    synced = 0
    for lang_file in translation_files:
        if os.path.basename(lang_file) == "TranslatedStrings_en.txt":
            continue

        try:
            updated = run_sync(ref_en_path, lang_file, output_dir)
            if updated:
                synced += 1
                print(c.success(f"✓ {os.path.basename(lang_file)}"))
        except Exception as e:
            print(c.error(f"✗ {os.path.basename(lang_file)}: {e}"))

    if synced > 0:
        print()
        print(c.success(f"✓ {synced} fichier(s) synchronisé(s) dans {output_dir}"))
        return True
    else:
        return False
