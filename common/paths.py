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
from typing import Optional, List


# Nom du dossier racine par défaut pour tous les outils i18n
DEFAULT_I18N_DIR = "__i18n_tmp__"

# Variable globale pour le nom du dossier (configurable)
_i18n_dir = DEFAULT_I18N_DIR

# Alias pour compatibilité avec le code existant
I18N_KIT_DIR = DEFAULT_I18N_DIR

# Format du timestamp : YYYYMMDD_HHMMSS (15 caractères)
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
TIMESTAMP_LENGTH = 15


def set_i18n_dir(name: str) -> None:
    """
    Définit le nom du dossier temporaire i18n.

    Args:
        name: Nom du dossier (ex: "__i18n_tmp__", "__i18n_kit__")
    """
    global _i18n_dir, I18N_KIT_DIR
    if name and name.strip():
        _i18n_dir = name.strip()
        I18N_KIT_DIR = _i18n_dir  # Maintenir compatibilité


def get_i18n_dir() -> str:
    """
    Retourne le nom du dossier temporaire i18n configuré.

    Returns:
        Nom du dossier (ex: "__i18n_tmp__")
    """
    return _i18n_dir


def get_i18n_kit_path(plugin_path: str) -> str:
    """
    Retourne le chemin du dossier temporaire i18n dans le plugin.

    Args:
        plugin_path: Chemin absolu vers le plugin Lightroom (.lrplugin)

    Returns:
        Chemin complet: <plugin_path>/<i18n_dir>

    Example:
        >>> get_i18n_kit_path("/path/to/plugin.lrplugin")
        '/path/to/plugin.lrplugin/__i18n_tmp__'
    """
    return os.path.join(plugin_path, get_i18n_dir())


def _extract_tool_prefix(tool_name: str) -> str:
    """
    Extrait le préfixe numérique du nom de l'outil en inspectant le stack.

    Cette fonction remonte la stack pour trouver le script appelant et
    extraire son préfixe numérique (ex: "1_" pour 1_Extractor).

    Args:
        tool_name: Nom de l'outil (Extractor, Applicator, etc.)

    Returns:
        Nom de l'outil avec préfixe si trouvé (ex: "1_Extractor"), sinon nom original
    """
    import inspect
    import re

    # Parcourir la stack pour trouver le script appelant
    for frame_info in inspect.stack():
        frame_filename = frame_info.filename

        # Chercher un dossier avec préfixe numérique dans le chemin
        # Pattern: /X_ToolName/ où X est 1 ou plusieurs chiffres
        match = re.search(r'[\\/](\d+)_([^\\/]+)[\\/]', frame_filename)

        if match:
            prefix = match.group(1)  # Le numéro (ex: "1", "2", "3", "9")
            folder_name = match.group(2)  # Le nom du dossier sans préfixe

            # Vérifier si le nom du dossier correspond au tool_name
            # (en ignorant la casse et les underscores vs espaces)
            normalized_folder = folder_name.lower().replace('_', '').replace('-', '')
            normalized_tool = tool_name.lower().replace('_', '').replace('-', '')

            if normalized_folder.startswith(normalized_tool) or normalized_tool.startswith(normalized_folder):
                return f"{prefix}_{tool_name}"

    # Si aucun préfixe trouvé, retourner le nom original
    return tool_name


def get_tool_output_path(plugin_path: str, tool_name: str, create: bool = True) -> str:
    """
    Retourne le chemin de sortie pour un outil avec timestamp.

    Crée un nouveau dossier horodaté à chaque exécution pour
    conserver l'historique des opérations.

    Le nom du dossier outil inclut automatiquement le préfixe numérique
    du dossier d'installation (ex: 1_Extractor, 2_Applicator, etc.).

    Args:
        plugin_path: Chemin vers le plugin Lightroom (.lrplugin)
        tool_name: Nom de l'outil (Extractor, Applicator, TranslationManager, Tools)
        create: Si True, crée le dossier. Si False, retourne juste le chemin.

    Returns:
        Chemin complet: <plugin>/__i18n_kit__/<prefix_tool_name>/<YYYYMMDD_HHMMSS>/

    Example:
        >>> get_tool_output_path("/path/to/plugin.lrplugin", "Extractor")
        '/path/to/plugin.lrplugin/__i18n_kit__/1_Extractor/20260129_143022'
    """
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    # Ajouter le préfixe numérique au nom de l'outil
    prefixed_tool_name = _extract_tool_prefix(tool_name)

    path = os.path.join(
        get_i18n_kit_path(plugin_path),
        prefixed_tool_name,
        timestamp
    )

    if create:
        os.makedirs(path, exist_ok=True)

    return path


def find_all_tool_outputs(plugin_path: str, tool_name: str) -> List[str]:
    """
    Trouve tous les dossiers horodatés pour un outil, triés du plus récent au plus ancien.

    Recherche parmi les dossiers horodatés (format YYYYMMDD_HHMMSS)
    et retourne tous les dossiers trouvés, triés par date décroissante.

    Supporte les dossiers avec et sans préfixe numérique
    (ex: "Extractor" ou "1_Extractor").

    Args:
        plugin_path: Chemin vers le plugin Lightroom
        tool_name: Nom de l'outil (Extractor, Applicator, etc.)

    Returns:
        Liste des chemins complets des dossiers trouvés, triés du plus récent au plus ancien.
        Liste vide si aucun dossier trouvé.

    Example:
        >>> find_all_tool_outputs("/path/to/plugin.lrplugin", "Extractor")
        ['/path/.../1_Extractor/20260129_143022', '/path/.../1_Extractor/20260129_120000']
    """
    import re

    i18n_kit = get_i18n_kit_path(plugin_path)

    if not os.path.exists(i18n_kit):
        return []

    # Chercher tous les dossiers qui correspondent au pattern: X_ToolName ou ToolName
    # où X peut être n'importe quel chiffre
    tool_dir = None
    normalized_tool = tool_name.lower().replace('_', '').replace('-', '')

    # Lister tous les dossiers dans __i18n_kit__
    for dir_name in os.listdir(i18n_kit):
        dir_path = os.path.join(i18n_kit, dir_name)
        if not os.path.isdir(dir_path):
            continue

        # Vérifier si c'est le bon outil (avec ou sans préfixe)
        # Pattern: X_ToolName ou ToolName
        match = re.match(r'^(\d+_)?(.+)$', dir_name)
        if match:
            folder_tool_name = match.group(2)
            normalized_folder = folder_tool_name.lower().replace('_', '').replace('-', '')

            if normalized_folder == normalized_tool or \
               normalized_folder.startswith(normalized_tool) or \
               normalized_tool.startswith(normalized_folder):
                tool_dir = dir_path
                break

    if not tool_dir or not os.path.exists(tool_dir):
        return []

    # Lister uniquement les dossiers au format YYYYMMDD_HHMMSS (15 caractères)
    dirs = [
        d for d in os.listdir(tool_dir)
        if os.path.isdir(os.path.join(tool_dir, d)) and len(d) == TIMESTAMP_LENGTH
    ]

    if not dirs:
        return []

    # Tri décroissant (le plus récent en premier)
    # Le format YYYYMMDD_HHMMSS permet un tri lexicographique correct
    dirs.sort(reverse=True)

    return [os.path.join(tool_dir, d) for d in dirs]


def find_latest_tool_output(plugin_path: str, tool_name: str) -> Optional[str]:
    """
    Trouve le dossier le plus récent pour un outil.

    Recherche parmi les dossiers horodatés (format YYYYMMDD_HHMMSS)
    et retourne le plus récent par tri lexicographique.

    Supporte les dossiers avec et sans préfixe numérique
    (ex: "Extractor" ou "1_Extractor").

    Args:
        plugin_path: Chemin vers le plugin Lightroom
        tool_name: Nom de l'outil (Extractor, Applicator, etc.)

    Returns:
        Chemin complet du dernier dossier, ou None si aucun trouvé

    Example:
        >>> find_latest_tool_output("/path/to/plugin.lrplugin", "Extractor")
        '/path/to/plugin.lrplugin/__i18n_kit__/1_Extractor/20260129_143022'
    """
    all_outputs = find_all_tool_outputs(plugin_path, tool_name)
    return all_outputs[0] if all_outputs else None


def is_valid_plugin_path(path: str) -> bool:
    """
    Vérifie si le chemin est un plugin Lightroom valide.

    Args:
        path: Chemin à vérifier

    Returns:
        True si le chemin se termine par .lrplugin et existe, False sinon
    """
    if not path:
        return False
    normalized = os.path.normpath(path)
    return os.path.isdir(normalized) and normalized.lower().endswith('.lrplugin')


def validate_plugin_path(path: str) -> tuple:
    """
    Valide un chemin de plugin et retourne des informations détaillées.

    Args:
        path: Chemin à valider

    Returns:
        Tuple (is_valid, normalized_path, warning_message)
        - is_valid: True si valide
        - normalized_path: Chemin normalisé
        - warning_message: Message d'avertissement ou None
    """
    if not path:
        return False, None, "Chemin vide"

    normalized = os.path.normpath(path)

    if not os.path.isdir(normalized):
        return False, normalized, f"Répertoire introuvable: {normalized}"

    if not normalized.lower().endswith('.lrplugin'):
        return True, normalized, "Ce dossier ne se termine pas par .lrplugin"

    return True, normalized, None


def normalize_path(path: str) -> str:
    """
    Normalise un chemin pour compatibilité Windows/Linux.

    - Convertit en chemin absolu
    - Normalise les séparateurs (/ ou \\ selon l'OS)
    - Résout les .. et .

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
