#!/usr/bin/env python3
"""
common/menu_helpers.py

Fonctions helper réutilisables pour les menus interactifs.

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-31
Version : 1.0
"""

import os
from typing import Optional
from common.paths import find_all_tool_outputs
from common.colors import Colors

# Instance couleurs
c = Colors()


def select_tool_output_dir(plugin_path: str, tool_name: str, current_dir: str = "") -> Optional[str]:
    """
    Affiche un menu interactif pour sélectionner un dossier de sortie d'un outil.

    Permet de :
    - Choisir parmi les dossiers timestampés disponibles (du plus récent au plus ancien)
    - Saisir manuellement un chemin personnalisé
    - Annuler et garder le dossier actuel

    Args:
        plugin_path: Chemin vers le plugin Lightroom
        tool_name: Nom de l'outil (Extractor, Applicator, etc.)
        current_dir: Dossier actuellement sélectionné (optionnel)

    Returns:
        Chemin du dossier sélectionné ou None si annulé

    Example:
        >>> dir = select_tool_output_dir(plugin_path, "Extractor", current_extraction)
        >>> if dir:
        >>>     self.extraction_dir = dir
    """
    print()
    print(c.title(f"Dossier {tool_name}"))
    print(c.separator())

    if current_dir:
        print(f"Actuel: {c.VALUE}{current_dir}{c.RESET}")
        print()

    # Récupérer tous les dossiers disponibles
    all_dirs = []
    if plugin_path and os.path.isdir(plugin_path):
        all_dirs = find_all_tool_outputs(plugin_path, tool_name)

    if len(all_dirs) > 1:
        # Plusieurs dossiers disponibles : afficher le menu de choix
        print(f"Dossiers {tool_name} disponibles (du plus récent au plus ancien):")
        print()
        for idx, dir_path in enumerate(all_dirs, 1):
            timestamp = os.path.basename(dir_path)
            marker = f"{c.OK}(dernier){c.RESET}" if idx == 1 else ""
            print(f"  {c.BOLD}{idx}{c.RESET}. {timestamp} {marker}")
            print(f"     {c.DIM}{dir_path}{c.RESET}")
        print()
        print(f"  {c.BOLD}M{c.RESET}. Saisir manuellement un autre répertoire")
        print(f"  {c.BOLD}0{c.RESET}. Annuler (garder actuel)")
        print()

        choice = input(c.prompt("Votre choix: ")).strip().upper()

        if choice == '0':
            print(c.success("Chemin inchangé"))
            return current_dir
        elif choice == 'M':
            manual_path = input(c.prompt("Chemin du répertoire: ")).strip()
            if manual_path and os.path.isdir(manual_path):
                print(c.success(f"Dossier: {manual_path}"))
                return manual_path
            elif manual_path:
                print(c.error("Répertoire introuvable"))
                return None
            else:
                print(c.success("Annulé"))
                return None
        elif choice.isdigit() and 1 <= int(choice) <= len(all_dirs):
            selected_dir = all_dirs[int(choice) - 1]
            print(c.success(f"Dossier sélectionné: {os.path.basename(selected_dir)}"))
            return selected_dir
        else:
            print(c.error("Choix invalide"))
            return None

    elif len(all_dirs) == 1:
        # Un seul dossier disponible
        auto_detect = all_dirs[0]
        print(f"Dossier auto-détecté: {c.VALUE}{auto_detect}{c.RESET}")
        print()
        print(f"  {c.BOLD}1{c.RESET}. Utiliser ce dossier")
        print(f"  {c.BOLD}M{c.RESET}. Saisir manuellement un autre répertoire")
        print(f"  {c.BOLD}0{c.RESET}. Annuler (garder actuel)")
        print()

        choice = input(c.prompt("Votre choix: ")).strip().upper()

        if choice == '0':
            print(c.success("Chemin inchangé"))
            return current_dir
        elif choice == '1' or choice == '':
            print(c.success(f"Dossier sélectionné: {os.path.basename(auto_detect)}"))
            return auto_detect
        elif choice == 'M':
            manual_path = input(c.prompt("Chemin du répertoire: ")).strip()
            if manual_path and os.path.isdir(manual_path):
                print(c.success(f"Dossier: {manual_path}"))
                return manual_path
            elif manual_path:
                print(c.error("Répertoire introuvable"))
                return None
            else:
                print(c.success("Annulé"))
                return None
        else:
            print(c.error("Choix invalide"))
            return None

    else:
        # Aucun dossier trouvé
        print(c.warning(f"Aucun dossier {tool_name} trouvé"))
        print()
        manual_path = input(c.prompt("Chemin du répertoire (ENTRÉE pour annuler): ")).strip()

        if manual_path:
            if os.path.isdir(manual_path):
                print(c.success(f"Dossier: {manual_path}"))
                return manual_path
            else:
                print(c.error("Répertoire introuvable"))
                return None
        else:
            print(c.success("Annulé"))
            return None
