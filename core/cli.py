#!/usr/bin/env python3
"""
Nom du fichier : cli.py

Dépendances : core.i18n

Description :
Éléments communs aux points d'entrée en ligne de commande : arguments argparse identiques dans
les outils (nom, aide, défaut) et effacement d'écran conditionné à la présence d'un terminal.

Usage CLI :
    Non pourvu

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import argparse
import os
import sys

from core.i18n import _


def add_default_plugin_arg(parser: argparse.ArgumentParser) -> None:
    """Ajoute --default-plugin (plugin pré-configuré du menu interactif)."""
    parser.add_argument('--default-plugin', default="",
                        help=_("Plugin pré-configuré pour le menu interactif"))


def add_plugin_path_arg(parser: argparse.ArgumentParser) -> None:
    """Ajoute --plugin-path (active le mode CLI de l'Extractor et de l'Applicator)."""
    parser.add_argument('--plugin-path', default=None,
                        help=_("Chemin vers le répertoire du plugin (active le mode CLI)"))


def clear_screen() -> None:
    """Efface l'écran, seulement si la sortie est un terminal (pas en CLI redirigée)."""
    if sys.stdout is not None and sys.stdout.isatty():
        os.system('cls' if os.name == 'nt' else 'clear')
