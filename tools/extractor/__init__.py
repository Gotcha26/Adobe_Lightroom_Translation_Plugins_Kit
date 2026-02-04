"""
Nom du fichier : __init__.py

Dépendances : .main, .menu

Description :
Package Extractor - Extraction des chaînes localisables des plugins Adobe Lightroom.
Ce module expose les fonctions principales pour lancer l'extraction via l'API ou le menu interactif.

Usage CLI :
    Non pourvu

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""
from .main import run_extraction
from .menu import show_interactive_menu
