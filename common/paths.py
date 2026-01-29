#!/usr/bin/env python3
"""
common/paths.py

Module commun pour gérer les chemins __i18n_kit__

Toutes les sorties des outils doivent être écrites dans :
    <plugin_lightroom>/__i18n_kit__/<Outil>/<timestamp_YYYYMMDD_HHMMSS>/

Fonctions :
    - get_i18n_kit_path(plugin_path) : Retourne le chemin __i18n_kit__
    - get_tool_output_path(plugin_path, tool_name, create=True) : Crée et retourne le dossier de sortie
    - find_latest_tool_output(plugin_path, tool_name) : Trouve le dernier dossier d'un outil
    - normalize_path(path) : Normalise un chemin (Windows/Linux)

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-29
Version : 1.0
"""

import os
from datetime import datetime
from typing import Optional


# Nom du dossier racine pour tous les outils i18n
I18N_KIT_DIR = "__i18n_kit__"

# Format du timestamp : YYYYMMDD_HHMMSS (15 caractères)
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
TIMESTAMP_LENGTH = 15


def get_i18n_kit_path(plugin_path: str) -> str:
    """
    Retourne le chemin du dossier __i18n_kit__ dans le plugin.

    Args:
        plugin_path: Chemin absolu vers le plugin Lightroom (.lrplugin)

    Returns:
        Chemin complet: <plugin_path>/__i18n_kit__

    Example:
        >>> get_i18n_kit_path("/path/to/plugin.lrplugin")
        '/path/to/plugin.lrplugin/__i18n_kit__'
    """
    return os.path.join(plugin_path, I18N_KIT_DIR)


def get_tool_output_path(plugin_path: str, tool_name: str, create: bool = True) -> str:
    """
    Retourne le chemin de sortie pour un outil avec timestamp.

    Crée un nouveau dossier horodaté à chaque exécution pour
    conserver l'historique des opérations.

    Args:
        plugin_path: Chemin vers le plugin Lightroom (.lrplugin)
        tool_name: Nom de l'outil (Extractor, Applicator, TranslationManager, Tools)
        create: Si True, crée le dossier. Si False, retourne juste le chemin.

    Returns:
        Chemin complet: <plugin>/__i18n_kit__/<tool_name>/<YYYYMMDD_HHMMSS>/

    Example:
        >>> get_tool_output_path("/path/to/plugin.lrplugin", "Extractor")
        '/path/to/plugin.lrplugin/__i18n_kit__/Extractor/20260129_143022'
    """
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    path = os.path.join(
        get_i18n_kit_path(plugin_path),
        tool_name,
        timestamp
    )

    if create:
        os.makedirs(path, exist_ok=True)

    return path


def find_latest_tool_output(plugin_path: str, tool_name: str) -> Optional[str]:
    """
    Trouve le dossier le plus récent pour un outil.

    Recherche parmi les dossiers horodatés (format YYYYMMDD_HHMMSS)
    et retourne le plus récent par tri lexicographique.

    Args:
        plugin_path: Chemin vers le plugin Lightroom
        tool_name: Nom de l'outil (Extractor, Applicator, etc.)

    Returns:
        Chemin complet du dernier dossier, ou None si aucun trouvé

    Example:
        >>> find_latest_tool_output("/path/to/plugin.lrplugin", "Extractor")
        '/path/to/plugin.lrplugin/__i18n_kit__/Extractor/20260129_143022'
    """
    tool_dir = os.path.join(get_i18n_kit_path(plugin_path), tool_name)

    if not os.path.exists(tool_dir):
        return None

    # Lister uniquement les dossiers au format YYYYMMDD_HHMMSS (15 caractères)
    dirs = [
        d for d in os.listdir(tool_dir)
        if os.path.isdir(os.path.join(tool_dir, d)) and len(d) == TIMESTAMP_LENGTH
    ]

    if not dirs:
        return None

    # Tri décroissant (le plus récent en premier)
    # Le format YYYYMMDD_HHMMSS permet un tri lexicographique correct
    dirs.sort(reverse=True)

    return os.path.join(tool_dir, dirs[0])


def normalize_path(path: str) -> str:
    """
    Normalise un chemin pour compatibilité Windows/Linux.

    - Convertit en chemin absolu
    - Normalise les separateurs (/ ou \\ selon l'OS)
    - Resout les .. et .

    Args:
        path: Chemin à normaliser (relatif ou absolu)

    Returns:
        Chemin absolu normalisé selon l'OS

    Example:
        >>> normalize_path("./plugin.lrplugin")
        '/current/dir/plugin.lrplugin'  # sur Linux
        'C:\\current\\dir\\plugin.lrplugin'  # sur Windows
    """
    return os.path.normpath(os.path.abspath(path))
