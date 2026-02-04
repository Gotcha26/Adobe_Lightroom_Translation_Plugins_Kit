"""
Extractor - Extraction des chaînes localisables des plugins Lightroom.

Ce module analyse les fichiers Lua d'un plugin et extrait toutes les
chaînes de texte pouvant être localisées.
"""
from .main import run_extraction
from .menu import show_interactive_menu
