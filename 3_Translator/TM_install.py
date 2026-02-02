#!/usr/bin/env python3
"""
TM_install.py

Installe les fichiers TranslatedStrings_xx.txt depuis la dernière extraction
vers la racine du plugin.

Cette commande est utile lors de la première initialisation du plugin multilingue.
Elle copie les fichiers générés par Extractor vers le plugin pour les rendre actifs.

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-01-31
Version: 1.0
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import find_latest_tool_output, get_tool_output_path
from common.colors import Colors

c = Colors()


def check_existing_translation_files(plugin_path: str) -> tuple[bool, list[str]]:
    """
    Vérifie si des fichiers TranslatedStrings_xx.txt existent déjà dans le plugin.

    Args:
        plugin_path: Chemin du plugin

    Returns:
        (bool, list): (True si fichiers existent, liste des fichiers trouvés)
    """
    existing_files = []

    if not os.path.isdir(plugin_path):
        return False, []

    for filename in os.listdir(plugin_path):
        if filename.startswith("TranslatedStrings_") and filename.endswith(".txt"):
            existing_files.append(filename)

    return len(existing_files) > 0, existing_files


def find_translation_files_in_extraction(extraction_dir: str) -> list[str]:
    """
    Trouve les fichiers TranslatedStrings_xx.txt dans un dossier d'extraction.

    Args:
        extraction_dir: Dossier d'extraction

    Returns:
        Liste des fichiers trouvés (chemins complets)
    """
    translation_files = []

    if not os.path.isdir(extraction_dir):
        return []

    for filename in os.listdir(extraction_dir):
        if filename.startswith("TranslatedStrings_") and filename.endswith(".txt"):
            full_path = os.path.join(extraction_dir, filename)
            translation_files.append(full_path)

    return translation_files


def install_translation_files(plugin_path: str, source_dir: str,
                             dry_run: bool = False) -> tuple[bool, list[str]]:
    """
    Installe les fichiers TranslatedStrings_xx.txt dans le plugin.

    Args:
        plugin_path: Chemin du plugin
        source_dir: Dossier source contenant les fichiers
        dry_run: Si True, simule sans copier

    Returns:
        (bool, list): (Succès, liste des fichiers installés)
    """
    # Trouver les fichiers à installer
    files_to_install = find_translation_files_in_extraction(source_dir)

    if not files_to_install:
        return False, []

    installed = []

    for file_path in files_to_install:
        filename = os.path.basename(file_path)
        dest_path = os.path.join(plugin_path, filename)

        if not dry_run:
            try:
                shutil.copy2(file_path, dest_path)
                installed.append(filename)
            except Exception as e:
                print(c.error(f"Erreur lors de la copie de {filename}: {e}"))
                return False, installed
        else:
            installed.append(filename)

    return True, installed


def menu_install(plugin_path: str):
    """Menu interactif pour l'installation des fichiers de traduction."""
    from TM_common import clear_screen, print_header

    clear_screen()
    print_header()

    print(f"\n{c.TITLE}  INSTALL - Installation des fichiers de traduction{c.RESET}")
    print(c.separator())

    # Vérifier si le plugin est configuré
    if not plugin_path or not os.path.isdir(plugin_path):
        print(c.error("Plugin non configuré ou introuvable."))
        return

    # Vérifier si des fichiers existent déjà
    has_files, existing = check_existing_translation_files(plugin_path)

    if has_files:
        print(f"\n{c.WARNING}[ATTENTION]{c.RESET} Des fichiers de traduction existent déjà:")
        for f in existing:
            print(f"  - {c.VALUE}{f}{c.RESET}")
        print()
        print("Cette commande est destinée à l'initialisation du plugin.")
        print("Pour mettre à jour des fichiers existants, utilisez SYNC.")
        print()
        choice = input(f"{c.PROMPT}Continuer quand même? (o/N): {c.RESET}").strip().lower()
        if choice not in ['o', 'oui', 'y', 'yes']:
            print(c.warning("Installation annulée"))
            return

    # Trouver la dernière extraction
    latest_extraction = find_latest_tool_output(plugin_path, "Extractor")

    if not latest_extraction:
        print(c.error("Aucune extraction trouvée."))
        print()
        print("Lancez d'abord l'Extractor pour générer TranslatedStrings_en.txt")
        return

    print(f"\n{c.INFO}[INFO]{c.RESET} Dernière extraction:")
    print(f"  {c.VALUE}{os.path.basename(latest_extraction)}{c.RESET}")
    print()

    # Trouver les fichiers disponibles
    files = find_translation_files_in_extraction(latest_extraction)

    if not files:
        print(c.error("Aucun fichier TranslatedStrings_xx.txt trouvé dans l'extraction."))
        return

    print(f"{c.INFO}Fichiers à installer:{c.RESET}")
    for f in files:
        print(f"  - {c.VALUE}{os.path.basename(f)}{c.RESET}")
    print()

    # Demander confirmation
    choice = input(f"{c.PROMPT}Installer ces fichiers dans le plugin? (O/n): {c.RESET}").strip().lower()

    if choice in ['n', 'non', 'no']:
        print(c.warning("Installation annulée"))
        return

    # Installer
    success, installed = install_translation_files(plugin_path, latest_extraction, dry_run=False)

    if success:
        print()
        print(c.success("✓ Installation réussie!"))
        print()
        print(f"{c.INFO}Fichiers installés:{c.RESET}")
        for f in installed:
            dest = os.path.join(plugin_path, f)
            print(f"  {c.VALUE}{f}{c.RESET}")
            print(f"    → {c.DIM}{dest}{c.RESET}")
        print()
        print(f"{c.INFO}Prochaines étapes:{c.RESET}")
        print("  1. Lancez l'Applicator pour remplacer les chaînes en dur par LOC()")
        print("  2. Testez le plugin dans Lightroom")
        print("  3. Créez des copies pour d'autres langues (TranslatedStrings_fr.txt, etc.)")
    else:
        print(c.error("Installation échouée"))


def run_install(plugin_path: str, source_dir: Optional[str] = None,
                dry_run: bool = False) -> bool:
    """
    Exécute l'installation (mode CLI).

    Args:
        plugin_path: Chemin du plugin
        source_dir: Dossier source (optionnel, auto-détecté sinon)
        dry_run: Simulation

    Returns:
        bool: Succès
    """
    if not plugin_path or not os.path.isdir(plugin_path):
        print(c.error("Chemin du plugin invalide"))
        return False

    # Auto-détecter le dossier source si non fourni
    if not source_dir:
        source_dir = find_latest_tool_output(plugin_path, "Extractor")
        if not source_dir:
            print(c.error("Aucune extraction trouvée"))
            return False

    # Vérifier si des fichiers existent déjà
    has_files, existing = check_existing_translation_files(plugin_path)
    if has_files:
        print(c.warning(f"Des fichiers existent déjà: {', '.join(existing)}"))

    # Installer
    success, installed = install_translation_files(plugin_path, source_dir, dry_run)

    if success:
        if dry_run:
            print(c.info(f"[DRY RUN] Fichiers qui seraient installés: {', '.join(installed)}"))
        else:
            print(c.success(f"✓ {len(installed)} fichier(s) installé(s): {', '.join(installed)}"))
        return True
    else:
        print(c.error("Installation échouée"))
        return False
