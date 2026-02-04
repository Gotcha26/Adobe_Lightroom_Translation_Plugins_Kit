"""
Nom du fichier : __init__.py

Dépendances : .main, .menu

Description :
Package Applicator pour l'application des localisations aux plugins Lightroom.
Remplace les chaînes extraites par les appels LOC appropriés au SDK Adobe Lightroom.

Usage CLI :
    Non pourvu

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""
from .main import process_plugin_directory
from .menu import show_interactive_menu
