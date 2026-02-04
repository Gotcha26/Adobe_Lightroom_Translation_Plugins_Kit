"""
Applicator - Application des localisations aux plugins Lightroom.

Ce module remplace les chaînes extraites par les appels LOC appropriés.
"""
from .main import process_plugin_directory
from .menu import show_interactive_menu
