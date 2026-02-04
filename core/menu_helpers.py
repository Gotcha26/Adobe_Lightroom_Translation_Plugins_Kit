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
from core.paths import find_all_tool_outputs
from core.colors import Colors
from core.i18n import _

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
    print(c.title(_("Dossier {tool}").format(tool=tool_name)))
    print(c.separator())

    if current_dir:
        print(_("Actuel:") + f" {c.VALUE}{current_dir}{c.RESET}")
        print()

    # Récupérer tous les dossiers disponibles
    all_dirs = []
    if plugin_path and os.path.isdir(plugin_path):
        all_dirs = find_all_tool_outputs(plugin_path, tool_name)

    if len(all_dirs) > 1:
        # Plusieurs dossiers disponibles : afficher le menu de choix
        print(_("Dossiers {tool} disponibles (du plus récent au plus ancien):").format(tool=tool_name))
        print()
        for idx, dir_path in enumerate(all_dirs, 1):
            timestamp = os.path.basename(dir_path)
            marker = f"{c.OK}" + _("(dernier)") + f"{c.RESET}" if idx == 1 else ""
            print(f"  {c.BOLD}{idx}{c.RESET}. {timestamp} {marker}")
            print(f"     {c.DIM}{dir_path}{c.RESET}")
        print()
        print(f"  {c.BOLD}M{c.RESET}. " + _("Saisir manuellement un autre répertoire"))
        print(f"  {c.BOLD}0{c.RESET}. " + _("Annuler (garder actuel)"))
        print()

        choice = input(c.prompt(_("Votre choix:") + " ")).strip().upper()

        if choice == '0':
            print(c.success(_("Chemin inchangé")))
            return current_dir
        elif choice == 'M':
            manual_path = input(c.prompt(_("Chemin du répertoire:") + " ")).strip()
            if manual_path and os.path.isdir(manual_path):
                print(c.success(_("Dossier: {path}").format(path=manual_path)))
                return manual_path
            elif manual_path:
                print(c.error(_("Répertoire introuvable")))
                return None
            else:
                print(c.success(_("Annulé")))
                return None
        elif choice.isdigit() and 1 <= int(choice) <= len(all_dirs):
            selected_dir = all_dirs[int(choice) - 1]
            print(c.success(_("Dossier sélectionné: {name}").format(name=os.path.basename(selected_dir))))
            return selected_dir
        else:
            print(c.error(_("Choix invalide")))
            return None

    elif len(all_dirs) == 1:
        # Un seul dossier disponible
        auto_detect = all_dirs[0]
        print(_("Dossier auto-détecté:") + f" {c.VALUE}{auto_detect}{c.RESET}")
        print()
        print(f"  {c.BOLD}1{c.RESET}. " + _("Utiliser ce dossier"))
        print(f"  {c.BOLD}M{c.RESET}. " + _("Saisir manuellement un autre répertoire"))
        print(f"  {c.BOLD}0{c.RESET}. " + _("Annuler (garder actuel)"))
        print()

        choice = input(c.prompt(_("Votre choix:") + " ")).strip().upper()

        if choice == '0':
            print(c.success(_("Chemin inchangé")))
            return current_dir
        elif choice == '1' or choice == '':
            print(c.success(_("Dossier sélectionné: {name}").format(name=os.path.basename(auto_detect))))
            return auto_detect
        elif choice == 'M':
            manual_path = input(c.prompt(_("Chemin du répertoire:") + " ")).strip()
            if manual_path and os.path.isdir(manual_path):
                print(c.success(_("Dossier: {path}").format(path=manual_path)))
                return manual_path
            elif manual_path:
                print(c.error(_("Répertoire introuvable")))
                return None
            else:
                print(c.success(_("Annulé")))
                return None
        else:
            print(c.error(_("Choix invalide")))
            return None

    else:
        # Aucun dossier trouvé
        print(c.warning(_("Aucun dossier {tool} trouvé").format(tool=tool_name)))
        print()
        manual_path = input(c.prompt(_("Chemin du répertoire (ENTRÉE pour annuler):") + " ")).strip()

        if manual_path:
            if os.path.isdir(manual_path):
                print(c.success(_("Dossier: {path}").format(path=manual_path)))
                return manual_path
            else:
                print(c.error(_("Répertoire introuvable")))
                return None
        else:
            print(c.success(_("Annulé")))
            return None
