#!/usr/bin/env python3
"""
Nom du fichier : menu_helpers.py

Dépendances : core.paths, core.colors, core.i18n

Description :
Fonctions helper réutilisables pour construire des menus interactifs dans le terminal. Offre
la sélection de répertoires, menus avec options numérotées, et validations d'entrée utilisateur.

Usage CLI :
    Non pourvu

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
from typing import Optional, Tuple
from core.paths import find_all_tool_outputs
from core.colors import c
from core.i18n import _



def choose_tool_output_dir(plugin_path: str, tool_name: str,
                           current_dir: str = "") -> Tuple[Optional[str], bool]:
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
        Tuple (chemin, annulé) :
        - (chemin du dossier sélectionné, False) ;
        - (`current_dir`, True) si l'utilisateur annule (peut être "") ;
        - (None, False) en cas d'erreur (chemin introuvable, choix invalide), déjà affichée.
        Re-sélectionner le dossier courant renvoie (current_dir, False) : seul
        `annulé` distingue ce cas d'une annulation.

    Example:
        >>> dir, cancelled = choose_tool_output_dir(plugin_path, "Extractor", current_extraction)
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
            return current_dir, True
        elif choice == 'M':
            manual_path = input(c.prompt(_("Chemin du répertoire:") + " ")).strip()
            if manual_path and os.path.isdir(manual_path):
                print(c.success(_("Dossier: {path}").format(path=manual_path)))
                return manual_path, False
            elif manual_path:
                print(c.error(_("Répertoire introuvable")))
                return None, False
            else:
                print(c.success(_("Annulé")))
                return current_dir, True
        elif choice.isdigit() and 1 <= int(choice) <= len(all_dirs):
            selected_dir = all_dirs[int(choice) - 1]
            print(c.success(_("Dossier sélectionné: {name}").format(name=os.path.basename(selected_dir))))
            return selected_dir, False
        else:
            print(c.error(_("Choix invalide")))
            return None, False

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
            return current_dir, True
        elif choice == '1' or choice == '':
            print(c.success(_("Dossier sélectionné: {name}").format(name=os.path.basename(auto_detect))))
            return auto_detect, False
        elif choice == 'M':
            manual_path = input(c.prompt(_("Chemin du répertoire:") + " ")).strip()
            if manual_path and os.path.isdir(manual_path):
                print(c.success(_("Dossier: {path}").format(path=manual_path)))
                return manual_path, False
            elif manual_path:
                print(c.error(_("Répertoire introuvable")))
                return None, False
            else:
                print(c.success(_("Annulé")))
                return current_dir, True
        else:
            print(c.error(_("Choix invalide")))
            return None, False

    else:
        # Aucun dossier trouvé
        print(c.warning(_("Aucun dossier {tool} trouvé").format(tool=tool_name)))
        print()
        manual_path = input(c.prompt(_("Chemin du répertoire (ENTRÉE pour annuler):") + " ")).strip()

        if manual_path:
            if os.path.isdir(manual_path):
                print(c.success(_("Dossier: {path}").format(path=manual_path)))
                return manual_path, False
            else:
                print(c.error(_("Répertoire introuvable")))
                return None, False
        else:
            print(c.success(_("Annulé")))
            return current_dir, True


def select_tool_output_dir(plugin_path: str, tool_name: str, current_dir: str = "") -> Optional[str]:
    """
    Variante de `choose_tool_output_dir` sans l'indicateur d'annulation.

    Returns:
        - le chemin du dossier sélectionné ;
        - `current_dir` inchangé si l'utilisateur annule (peut être "") ;
        - None en cas d'erreur (chemin introuvable, choix invalide), déjà affichée.
    """
    return choose_tool_output_dir(plugin_path, tool_name, current_dir)[0]
